import json
import os
import re
from datetime import date, datetime, timedelta
from functools import wraps

import requests
from flask import render_template, request, redirect, url_for, abort, flash, jsonify
from flask_login import current_user, login_user, login_required, logout_user
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from app import app, db
from app.form import CadastroUsuario, CadastroLivro, EditarLivro, LoginForm, CategoriaForm, SugestaoLivroForm
from app.models import Livro, Emprestimo, Usuario, PerfilEnum, Categoria, BookSuggestion

# Detecta caracteres de escritas não-latinas (japonês, chinês, coreano, árabe,
# cirílico, tailandês) para evitar sugerir títulos/autores nesses idiomas
# quando a busca é feita em português.
_PADRAO_NAO_LATINO = re.compile(
    r'[\u3040-\u30ff\u4e00-\u9fff\uac00-\ud7af\u0600-\u06ff\u0400-\u04ff\u0e00-\u0e7f]'
)


def _tem_script_nao_latino(texto):
    return bool(_PADRAO_NAO_LATINO.search(texto or ''))


# ── helpers ──────────────────────────────────────────────────────────────────

def perfil_requerido(*perfis):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.perfil not in perfis:
                abort(403)
            return f(*args, **kwargs)

        return decorated_function

    return decorator


# ── public ───────────────────────────────────────────────────────────────────

@app.route('/')
def home():
    return redirect(url_for('acervo'))


@app.route('/acervo', methods=['GET'])
def acervo():
    busca = request.args.get('busca', '')
    categoria_id = request.args.get('categoria', '')
    ordenar = request.args.get('ordenar', 'titulo')

    query = Livro.query

    if busca:
        query = query.filter(
            or_(
                Livro.titulo.ilike(f'%{busca}%'),
                Livro.autor.ilike(f'%{busca}%'),
                Livro.editora.ilike(f'%{busca}%')
            )
        )

    if categoria_id:
        query = query.filter(Livro.categoria_id == categoria_id)

    if ordenar == 'titulo':
        query = query.order_by(Livro.titulo.asc())
    elif ordenar == 'autor':
        query = query.order_by(Livro.autor.asc())
    elif ordenar == 'editora':
        query = query.order_by(Livro.editora.asc())
    elif ordenar == 'novo':
        query = query.order_by(Livro.ano.desc())
    elif ordenar == 'antigo':
        query = query.order_by(Livro.ano.asc())

    livros = query.all()
    categorias = Categoria.query.order_by(Categoria.nome).all()

    return render_template('acervo.html', livros=livros, categorias=categorias,
                           busca=busca, categoria_id=categoria_id, ordenar=ordenar)


@app.route('/livro/<int:id>')
def detalhe_livro(id):
    livro = Livro.query.get_or_404(id)
    return render_template('detalhe_livro.html', livro=livro)


# ── auth ─────────────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home_usuario'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.senha.data):
            login_user(user)
            return redirect(url_for('home_usuario'))
        flash('E-mail ou senha inválidos.', 'danger')
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route('/inicio')
@login_required
def home_usuario():
    if current_user.perfil == PerfilEnum.ADMIN:
        return redirect(url_for('menu'))
    elif current_user.perfil == PerfilEnum.PROFESSOR:
        return redirect(url_for('painel_professor'))
    else:
        return redirect(url_for('painel_aluno'))


# ── admin menu ────────────────────────────────────────────────────────────────

@app.route('/menu')
@login_required
@perfil_requerido(PerfilEnum.ADMIN)
def menu():
    return render_template('menu.html')


# ── cadastro de usuário ───────────────────────────────────────────────────────

@app.route("/cadastro", methods=["GET", "POST"])
@login_required
@perfil_requerido(PerfilEnum.ADMIN)
def cadastro():
    form = CadastroUsuario()
    form.perfil.choices = [
        ("aluno", "Aluno"),
        ("professor", "Professor"),
        ("admin", "Administrador")
    ]
    if form.validate_on_submit():
        if Usuario.query.filter_by(email=form.email.data).first():
            flash('E-mail já cadastrado.', 'danger')
            return render_template("cadastro.html", form=form)

        user = Usuario(
            nome=form.nome.data,
            sobrenome=form.sobrenome.data,
            email=form.email.data,
            perfil=PerfilEnum(form.perfil.data)
        )
        user.set_password(form.senha.data)
        db.session.add(user)
        db.session.commit()
        flash(f'Usuário {user.nome} cadastrado com sucesso!', 'success')
        return redirect(url_for('cadastro'))
    return render_template("cadastro.html", form=form)


# Palavras-chave (em inglês, como aparecem nos "subjects" da Open Library)
# mapeadas para as categorias em português usadas no sistema.
_MAPA_ASSUNTOS = [
    (['fantasy'], 'Fantasia'),
    (['science fiction', 'sci-fi', 'sci fi'], 'Ficção Científica'),
    (['dystopia', 'dystopian'], 'Distopia'),
    (['suspense'], 'Suspense'),
    (['thriller'], 'Thriller'),
    (['horror'], 'Terror'),
    (['action and adventure', 'action fiction'], 'Ação'),
    (['adventure'], 'Aventura'),
    (['love stories', 'romance'], 'Romance'),
    (['drama', 'plays'], 'Drama'),
    (['poetry', 'poems'], 'Poesia'),
    (['short stories'], 'Conto'),
    (['detective', 'mystery', 'crime'], 'Policial'),
    (['historical fiction', 'history'], 'Histórico'),
    (['biography', 'autobiography'], 'Biografia'),
    (['self-help', 'self help'], 'Autoajuda'),
    (['juvenile fiction', 'young adult'], 'Juvenil'),
    (['children'], 'Infantil'),
    (['fiction'], 'Ficção'),
    (['nonfiction', 'non-fiction'], 'Não Ficção'),
]


def _traduzir_assunto_para_categoria(assuntos):
    for assunto in assuntos:
        assunto_lower = assunto.lower()
        for palavras_chave, categoria_pt in _MAPA_ASSUNTOS:
            if any(p in assunto_lower for p in palavras_chave):
                return categoria_pt
    return None


def _buscar_openlibrary(titulo_busca, restringir_portugues=False):
    query = titulo_busca
    if restringir_portugues:
        query = f'{titulo_busca} language:por'

    resposta = requests.get(
        'https://openlibrary.org/search.json',
        params={
            'q': query,
            'limit': 20,
            'fields': 'key,title,author_name,first_publish_year,isbn,publisher,language,subject'
        },
        timeout=8
    )
    resposta.raise_for_status()
    return resposta.json().get('docs') or []


def _buscar_edicao_em_portugues(work_key):
    """
    Busca, dentre todas as edições de uma obra na Open Library, uma que esteja
    catalogada em português — trazendo o título, editora, ano e ISBN reais
    dessa edição (não o título "canônico" da obra, que costuma vir no idioma
    original).
    """
    if not work_key:
        return None
    try:
        resposta = requests.get(
            f'https://openlibrary.org{work_key}/editions.json',
            params={'limit': 50},
            timeout=4
        )
        resposta.raise_for_status()
        entradas = resposta.json().get('entries') or []
    except Exception:
        return None

    for edicao in entradas:
        idiomas = edicao.get('languages') or []
        codigos = [(i.get('key') or '').split('/')[-1] for i in idiomas]
        if 'por' not in codigos:
            continue

        titulo = (edicao.get('title') or '').strip()
        if not titulo or _tem_script_nao_latino(titulo):
            continue

        editoras = edicao.get('publishers') or []
        editora = editoras[0] if editoras else ''

        publish_date = edicao.get('publish_date') or ''
        ano_match = re.search(r'(\d{4})', publish_date)
        ano = int(ano_match.group(1)) if ano_match else ''

        isbns_13 = edicao.get('isbn_13') or []
        isbns_10 = edicao.get('isbn_10') or []
        isbn = isbns_13[0] if isbns_13 else (isbns_10[0] if isbns_10 else '')

        return {'titulo': titulo, 'editora': editora, 'ano': ano, 'isbn': isbn}

    return None


# ── IA - preenchimento automático de livro ─────────────────────────────────────

@app.route('/api/buscar_livro_ia', methods=['POST'])
@login_required
@perfil_requerido(PerfilEnum.ADMIN)
def buscar_livro_ia():
    dados = request.get_json(silent=True) or {}
    titulo_busca = (dados.get('titulo') or '').strip()

    if not titulo_busca:
        return jsonify({'erro': 'Digite o nome do livro ou do autor para pesquisar.'}), 400

    categorias = Categoria.query.order_by(Categoria.nome).all()

    # 1ª tentativa: restringir a resultados com edição em português
    docs = []
    try:
        docs = _buscar_openlibrary(titulo_busca, restringir_portugues=True)
    except Exception:
        docs = []

    encontrado_em_portugues = bool(docs)

    # 2ª tentativa: busca geral, se não houver edição em português catalogada
    if not docs:
        try:
            docs = _buscar_openlibrary(titulo_busca, restringir_portugues=False)
        except Exception:
            return jsonify({
                'erro': 'Não foi possível consultar a base de livros agora. Tente novamente em instantes.'
            }), 502

    if not docs:
        return jsonify({'erro': 'Nenhum livro encontrado com esse nome.'}), 404

    def prioridade(doc):
        idiomas = doc.get('language') or []
        if 'por' in idiomas:
            prioridade_idioma = 0
        elif 'eng' in idiomas:
            prioridade_idioma = 1
        else:
            prioridade_idioma = 2

        texto_titulo = doc.get('title', '') or ''
        texto_autor = ' '.join(doc.get('author_name') or [])
        script_nao_latino = _tem_script_nao_latino(texto_titulo) or _tem_script_nao_latino(texto_autor)

        return (1 if script_nao_latino else 0, prioridade_idioma)

    docs_ordenados = sorted(docs, key=prioridade)

    resultados = []
    vistos = set()
    consultas_edicao_feitas = 0
    LIMITE_CONSULTAS_EDICAO = 6

    for doc in docs_ordenados:
        titulo = (doc.get('title') or '').strip()
        autores = doc.get('author_name') or []
        autor = ', '.join(autores)

        if not titulo:
            continue
        chave = (titulo.lower(), autor.lower())
        if chave in vistos:
            continue
        vistos.add(chave)

        editoras = doc.get('publisher') or []
        editora = editoras[0] if editoras else ''
        ano = doc.get('first_publish_year') or ''

        isbns = doc.get('isbn') or []
        isbn = ''
        if isbns:
            isbn_13 = next((i for i in isbns if len(i) == 13), None)
            isbn = isbn_13 or isbns[0]

        em_portugues = False

        # Se a obra tem alguma edição em português catalogada, busca os dados
        # reais dessa edição (título traduzido, editora e ISBN da tradução).
        if 'por' in (doc.get('language') or []) and consultas_edicao_feitas < LIMITE_CONSULTAS_EDICAO:
            consultas_edicao_feitas += 1
            edicao_pt = _buscar_edicao_em_portugues(doc.get('key'))
            if edicao_pt:
                titulo = edicao_pt['titulo'] or titulo
                editora = edicao_pt['editora'] or editora
                ano = edicao_pt['ano'] or ano
                isbn = edicao_pt['isbn'] or isbn
                em_portugues = True

        # Se, mesmo sem edição em português confirmada, o título/autor ainda
        # tiver escrita não-latina, pula este resultado (não é útil ao admin).
        if _tem_script_nao_latino(titulo) or _tem_script_nao_latino(autor):
            continue

        subjects = doc.get('subject') or []
        categoria_nome_sugerida = _traduzir_assunto_para_categoria(subjects) or ''
        categoria_id = None
        if categoria_nome_sugerida:
            correspondente = next(
                (c for c in categorias if c.nome.lower() == categoria_nome_sugerida.lower()),
                None
            )
            if correspondente:
                categoria_id = correspondente.id
                categoria_nome_sugerida = correspondente.nome

        resultados.append({
            'titulo': titulo,
            'autor': autor,
            'editora': editora,
            'ano': ano,
            'isbn': isbn,
            'categoria_id': categoria_id,
            'categoria_nome': categoria_nome_sugerida,
            'em_portugues': em_portugues
        })

        if len(resultados) >= 8:
            break

    if not resultados:
        return jsonify({'erro': 'Nenhum livro encontrado com esse nome.'}), 404

    aviso = None
    if not encontrado_em_portugues:
        aviso = ('Não encontramos edições em português catalogadas para esta busca. '
                 'Os resultados abaixo podem estar em outro idioma — revise antes de salvar.')

    return jsonify({
        'resultados': resultados,
        'aviso': aviso
    })


# ── livros ────────────────────────────────────────────────────────────────────

@app.route('/cadastrar_livro', methods=['GET', 'POST'])
@login_required
@perfil_requerido(PerfilEnum.ADMIN)
def cadastrar_livro():
    form = CadastroLivro()
    form_categoria = CategoriaForm()
    categorias = Categoria.query.order_by(Categoria.nome).all()
    form.categoria.choices = [(c.id, c.nome) for c in categorias]

    if form.validate_on_submit():
        if Livro.query.filter_by(isbn=form.isbn.data).first():
            flash('ISBN já cadastrado.', 'danger')
            return render_template('cadastrar_livro.html', form=form, form_categoria=form_categoria)

        if form.quantidade.data < 0:
            flash('Quantidade não pode ser negativa.', 'danger')
            return render_template('cadastrar_livro.html', form=form, form_categoria=form_categoria)

        livro = Livro(
            isbn=form.isbn.data,
            titulo=form.titulo.data,
            autor=form.autor.data,
            categoria_id=form.categoria.data,
            editora=form.editora.data,
            ano=form.ano.data,
            quantidade=form.quantidade.data,
            disponiveis=form.quantidade.data
        )
        db.session.add(livro)
        db.session.commit()
        flash('Livro cadastrado com sucesso!', 'success')
        return redirect(url_for('acervo'))

    return render_template('cadastrar_livro.html', form=form, form_categoria=form_categoria)


@app.route('/editar_livro/<int:id>', methods=['GET', 'POST'])
@login_required
@perfil_requerido(PerfilEnum.ADMIN)
def editar_livro(id):
    livro = Livro.query.get_or_404(id)
    form = EditarLivro()
    categorias = Categoria.query.order_by(Categoria.nome).all()
    form.categoria.choices = [(c.id, c.nome) for c in categorias]

    if form.validate_on_submit():
        existente = Livro.query.filter_by(isbn=form.isbn.data).first()
        if existente and existente.id != id:
            flash('ISBN já usado por outro livro.', 'danger')
            return render_template('editar_livro.html', form=form, livro=livro)

        diferenca = form.quantidade.data - livro.quantidade
        livro.isbn = form.isbn.data
        livro.titulo = form.titulo.data
        livro.autor = form.autor.data
        livro.categoria_id = form.categoria.data
        livro.editora = form.editora.data
        livro.ano = form.ano.data
        livro.quantidade = form.quantidade.data
        livro.disponiveis = max(0, (livro.disponiveis or 0) + diferenca)

        db.session.commit()
        flash('Livro atualizado!', 'success')
        return redirect(url_for('acervo'))

    form.isbn.data = livro.isbn
    form.titulo.data = livro.titulo
    form.autor.data = livro.autor
    form.categoria.data = livro.categoria_id
    form.editora.data = livro.editora
    form.ano.data = livro.ano
    form.quantidade.data = livro.quantidade

    return render_template('editar_livro.html', form=form, livro=livro)


@app.route('/excluir_livro/<int:id>')
@login_required
@perfil_requerido(PerfilEnum.ADMIN)
def excluir_livro(id):
    livro = Livro.query.get_or_404(id)
    # Impede exclusão se houver empréstimos ativos
    active_loans = Emprestimo.query.filter_by(livro_id=livro.id, devolucao=False).count()
    if active_loans > 0:
        flash('Não é possível excluir livro com empréstimos ativos.', 'danger')
        return redirect(url_for('acervo'))

    db.session.delete(livro)
    db.session.commit()
    flash('Livro excluído.', 'success')
    return redirect(url_for('acervo'))


# ── categoria ─────────────────────────────────────────────────────────────────

@app.route("/categoria/nova", methods=["POST"])
@login_required
@perfil_requerido(PerfilEnum.ADMIN)
def nova_categoria():
    nome = request.form.get("nome", "").strip()
    if nome:
        if not Categoria.query.filter_by(nome=nome.capitalize()).first():
            db.session.add(Categoria(nome=nome.capitalize()))
            db.session.commit()
            flash(f'Categoria "{nome.capitalize()}" criada!', 'success')
        else:
            flash('Categoria já existe.', 'warning')
    return redirect(url_for("cadastrar_livro"))


# ── empréstimo ────────────────────────────────────────────────────────────────

@app.route('/emprestimo', methods=['GET', 'POST'])
@login_required
@perfil_requerido(PerfilEnum.ADMIN)
def emprestimo():
    livros = Livro.query.order_by(Livro.titulo).all()
    usuarios = Usuario.query.filter(
        Usuario.perfil.in_([PerfilEnum.ALUNO, PerfilEnum.PROFESSOR])
    ).order_by(Usuario.nome).all()

    if request.method == 'POST':
        usuario_id = request.form.get('usuario')
        livro_id = request.form.get('livro')

        usuario = Usuario.query.get_or_404(usuario_id)
        livro = Livro.query.get_or_404(livro_id)

        emprestimos_ativos = Emprestimo.query.filter_by(
            usuario_id=usuario.id, devolucao=False
        ).count()

        limite = 3 if usuario.perfil == PerfilEnum.ALUNO else 5

        if emprestimos_ativos >= limite:
            flash(
                f'{usuario.nome} já atingiu o limite de {limite} livro(s) emprestado(s).',
                'danger'
            )
            return redirect(url_for('emprestimo'))

        if livro.disponiveis is None:
            livro.disponiveis = livro.quantidade

        if livro.disponiveis <= 0:
            flash('Não há exemplares disponíveis para este livro.', 'danger')
            return redirect(url_for('emprestimo'))

        dias = 7 if usuario.perfil == PerfilEnum.ALUNO else 15

        novo_emprestimo = Emprestimo(
            usuario_id=usuario.id,
            livro_id=livro.id,
            data_emprestimo=datetime.utcnow(),
            data_devolucao=datetime.utcnow() + timedelta(days=dias)
        )

        livro.disponiveis -= 1
        db.session.add(novo_emprestimo)
        db.session.commit()
        flash(f'Empréstimo registrado! Devolução em {dias} dias.', 'success')
        return redirect(url_for('emprestimo'))

    return render_template('emprestimo.html', livros=livros, usuarios=usuarios)


@app.route('/devolver/<int:id>')
@login_required
@perfil_requerido(PerfilEnum.ADMIN)
def devolver(id):
    emp = Emprestimo.query.get_or_404(id)
    if not emp.devolucao:
        emp.devolucao = True
        if emp.livro:  # Proteção contra livro excluído
            emp.livro.disponiveis = (emp.livro.disponiveis or 0) + 1
        db.session.commit()
        flash('Devolução registrada com sucesso!', 'success')
    return redirect(url_for('relatorio'))


# ── painéis de usuário ────────────────────────────────────────────────────────

@app.route('/painel_aluno')
@login_required
@perfil_requerido(PerfilEnum.ALUNO)
def painel_aluno():
    hoje = datetime.utcnow()
    emprestimos = Emprestimo.query.filter_by(
        usuario_id=current_user.id, devolucao=False
    ).all()
    return render_template('painel_aluno.html', emprestimos=emprestimos, hoje=hoje)


@app.route('/painel_professor', methods=['GET', 'POST'])
@login_required
@perfil_requerido(PerfilEnum.PROFESSOR)
def painel_professor():
    hoje = datetime.utcnow()
    emprestimos = Emprestimo.query.filter_by(
        usuario_id=current_user.id, devolucao=False
    ).all()

    form = SugestaoLivroForm()
    if form.validate_on_submit():
        sug = BookSuggestion(
            titulo=form.titulo.data,
            autor=form.autor.data,
            professor_id=current_user.id
        )
        db.session.add(sug)
        db.session.commit()
        flash('Sugestão enviada para o bibliotecário!', 'success')
        return redirect(url_for('painel_professor'))

    sugestoes = BookSuggestion.query.filter_by(professor_id=current_user.id).all()
    return render_template('painel_professor.html', emprestimos=emprestimos,
                           hoje=hoje, form=form, sugestoes=sugestoes)


# ── relatório ─────────────────────────────────────────────────────────────────

@app.route('/relatorio')
@login_required
@perfil_requerido(PerfilEnum.ADMIN)
def relatorio():
    hoje = datetime.utcnow()

    # 1. Captura o termo de busca digitado no input (name="busca")
    busca = request.args.get('busca', '').strip()

    categorias = Categoria.query.all()
    livros_por_categoria = [
        {'nome': c.nome, 'total': len(c.livros)} for c in categorias
    ]

    # 2. Cria as queries base para Ativos e Histórico
    query_ativos = Emprestimo.query.options(joinedload(Emprestimo.livro), joinedload(Emprestimo.usuario)).filter_by(devolucao=False)
    query_historico = Emprestimo.query.options(joinedload(Emprestimo.livro), joinedload(Emprestimo.usuario)).filter_by(devolucao=True)

    # 3. Se o usuário digitou algo na busca, aplica os filtros relacionais
    if busca:
        filtro_pesquisa = or_(
            Usuario.nome.ilike(f'%{busca}%'),
            Usuario.sobrenome.ilike(f'%{busca}%'),
            Livro.titulo.ilike(f'%{busca}%')
        )
        # É necessário dar .join() explicitamente nas tabelas para que o filtro funcione
        query_ativos = query_ativos.join(Emprestimo.usuario).join(Emprestimo.livro).filter(filtro_pesquisa)
        query_historico = query_historico.join(Emprestimo.usuario).join(Emprestimo.livro).filter(filtro_pesquisa)

    # 4. Executa as queries com os filtros aplicados (se houverem)
    emprestimos_ativos = query_ativos.all()
    historico_emprestimos = query_historico.order_by(Emprestimo.id.desc()).all()

    total_emprestimos = len(emprestimos_ativos)
    atrasados = [e for e in emprestimos_ativos if e.data_devolucao and e.data_devolucao < hoje]
    sugestoes = BookSuggestion.query.all()

    # 5. Retorna os dados, incluindo a variável 'busca' para manter o texto no input
    return render_template(
        'relatorio.html',
        livros_por_categoria=livros_por_categoria,
        total_emprestimos=total_emprestimos,
        emprestimos=emprestimos_ativos,
        historico=historico_emprestimos,
        atrasados=atrasados,
        sugestoes=sugestoes,
        hoje=hoje,
        busca=busca
    )

