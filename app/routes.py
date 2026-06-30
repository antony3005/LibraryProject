from datetime import date, datetime, timedelta
from functools import wraps

from flask import render_template, request, redirect, url_for, abort, flash
from flask_login import current_user, login_user, login_required, logout_user
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from app import app, db
from app.form import CadastroUsuario, CadastroLivro, EditarLivro, LoginForm, CategoriaForm, SugestaoLivroForm
from app.models import Livro, Emprestimo, Usuario, PerfilEnum, Categoria, BookSuggestion


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

    categorias = Categoria.query.all()
    livros_por_categoria = [
        {'nome': c.nome, 'total': len(c.livros)} for c in categorias
    ]

    # Carrega o livro junto para evitar erro se livro foi excluído
    emprestimos_ativos = Emprestimo.query.options(joinedload(Emprestimo.livro)) \
        .filter_by(devolucao=False).all()
    
    historico_emprestimos = Emprestimo.query.options(joinedload(Emprestimo.livro)) \
        .filter_by(devolucao=True).order_by(Emprestimo.id.desc()).all()

    total_emprestimos = len(emprestimos_ativos)
    atrasados = [e for e in emprestimos_ativos if e.data_devolucao and e.data_devolucao < hoje]
    sugestoes = BookSuggestion.query.all()

    return render_template(
        'relatorio.html',
        livros_por_categoria=livros_por_categoria,
        total_emprestimos=total_emprestimos,
        emprestimos=emprestimos_ativos,
        historico=historico_emprestimos,
        atrasados=atrasados,
        sugestoes=sugestoes,
        hoje=hoje
    )