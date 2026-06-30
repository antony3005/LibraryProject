from datetime import date, timedelta
from functools import wraps

from flask import render_template, request, redirect, url_for, abort, flash
from flask_login import current_user, login_user, login_required, logout_user
from sqlalchemy import or_

from app import app, db
from app.form import CadastroUsuario, CadastroLivro, EditarLivro, LoginForm, CategoriaForm
from app.models import Livro, Emprestimo, Usuario, PerfilEnum, Categoria


@app.route('/')
def home():
    return redirect(url_for('acervo'))


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


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():

        email = form.email.data
        senha = form.senha.data

        user = Usuario.query.filter_by(email=email).first()

        if user and user.check_password(senha):
            login_user(user)
            return redirect(url_for("acervo"))

        return "Login inválido", 401

    return render_template("login.html", form=form)


@app.route('/menu')
@login_required
@perfil_requerido(PerfilEnum.ADMIN)
def menu():
    return render_template('menu.html')


@app.route('/acervo', methods=['GET'])
def acervo():
    busca = request.args.get('busca', '')
    status = request.args.get('status', '')
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

    # Filtro de disponibilidade
    if status == 'disponivel':
        query = query.filter(Livro.disponivel == True)

    elif status == 'emprestado':
        query = query.filter(Livro.disponivel == False)

    # Ordenação
    if ordenar == 'titulo':
        query = query.order_by(Livro.titulo.asc())

    elif ordenar == 'autor':
        query = query.order_by(Livro.autor.asc())

    elif ordenar == 'editora':
        query = query.order_by(Livro.editora.asc())

    livros = query.all()
    categoria = Categoria.query.filter_by()
    return render_template(
        'acervo.html',
        livros=livros
    )


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route('/editar_livro/<int:id>', methods=['GET', 'POST'])
@login_required
@perfil_requerido(PerfilEnum.ADMIN)
def editar_livro(id):
    livro = Livro.query.get_or_404(id)
    form = EditarLivro()
    if form.validate_on_submit():
        livro = Livro(
            isbn=form.isbn.data,
            titulo=form.titulo.data,
            autor=form.autor.data,
            categoria=form.categoria.data,
            editora=form.editora.data,
            ano=form.ano.data,
            quantidade=form.quantidade.data,
            disponiveis=form.quantidade.data
        )

        db.session.add(livro)
        db.session.commit()

        return redirect(url_for('acervo'))

    return render_template('editar_livro.html', form=form, livro=livro)


@app.route('/excluir_livro/<int:id>')
@login_required
@perfil_requerido(PerfilEnum.ADMIN)
def excluir_livro(id):
    livro = Livro.query.get_or_404(id)

    db.session.delete(livro)
    db.session.commit()

    return redirect(url_for('acervo'))


@app.route('/emprestimo', methods=['GET', 'POST'])
@login_required
@perfil_requerido(PerfilEnum.ADMIN)
def emprestimo():
    livros = Livro.query.all()
    usuarios = Usuario.query.all()

    if request.method == 'POST':

        usuario_id = request.form['usuario']
        livro_id = request.form['livro']

        if not usuario_id:
            flash("Selecione um usuário.", "error")
            return redirect(url_for("emprestimo"))

        if not livro_id:
            flash("Selecione um livro.", "error")
            return redirect(url_for("emprestimo"))

        usuario = Usuario.query.get_or_404(usuario_id)
        livro = Livro.query.get_or_404(livro_id)

        emprestimos = Emprestimo.query.filter_by(
            usuario_id=usuario.id,
            devolucao=False
        ).count()
        print("Quantidade:", emprestimos)
        if emprestimos >= 3 and usuario.perfil == PerfilEnum.ALUNO or emprestimos >= 5 and usuario.perfil == PerfilEnum.PROFESSOR:
            flash(
                "Este usuário já possui o limite máximo de 3 livros emprestados.",
                "error"
            )
            return redirect(url_for("emprestimo"))
        print("rodou aqui ó")
        dias = 0
        if usuario.perfil == PerfilEnum.ALUNO:
            dias = 7
        elif usuario.perfil == PerfilEnum.PROFESSOR:
            dias = 15
        else:
            dias = 30
        if livro.disponiveis is None:
            livro.disponiveis = livro.quantidade

        if livro.disponiveis <= 0:
            flash(
                f"O livro '{livro.titulo}' não possui exemplares disponíveis.",
                "error"
            )
            return redirect(url_for("emprestimo"))

        novo_emprestimo = Emprestimo(
            usuario_id=int(usuario.id),
            livro_id=int(livro_id),
            data_emprestimo=date.today(),
            data_devolucao=date.today() + timedelta(days=dias)
        )

        livro.disponiveis -= 1

        db.session.add(novo_emprestimo)
        db.session.commit()

        return redirect(url_for('acervo'))

    return render_template(
        'emprestimo.html',
        livros=livros,
        usuarios=usuarios

    )


@app.route('/cadastrar_livro', methods=['GET', 'POST'])
@login_required
@perfil_requerido(PerfilEnum.ADMIN)
def cadastrar_livro():
    form = CadastroLivro()
    form_categoria = CategoriaForm()

    categoria = Categoria.query.all()

    form.categoria.choices = [(c.id, c.nome) for c in categoria]

    if form.validate_on_submit():
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
        flash("Livro cadastrado", "success")
        return redirect(url_for('acervo'))

    return render_template('cadastrar_livro.html', form=form, form_categoria=form_categoria)


@app.route("/cadastro", methods=["GET", "POST"])
@login_required
@perfil_requerido(PerfilEnum.ADMIN)
def cadastro():
    form = CadastroUsuario()

    form.perfil.choices = [
        ("aluno", "Aluno"),
        ("professor", "Professor"),
        ("admin", "Admin")
    ]

    if form.validate_on_submit():
        user = Usuario(
            nome=form.nome.data,
            sobrenome=form.sobrenome.data,
            email=form.email.data,
            perfil=PerfilEnum(form.perfil.data)
        )

        user.set_password(form.senha.data)

        db.session.add(user)
        db.session.commit()

        flash("Usuário Cadastrado", "success")
        return redirect(url_for("cadastro"))

    return render_template("cadastro.html", form=form)


@app.route("/alunos")
@login_required
@perfil_requerido(PerfilEnum.ADMIN)
def alunos():
    alunos = Usuario.query.filter(Usuario.perfil == "ALUNO").all()
    return render_template("painel_aluno.html", alunos=alunos)


@app.route('/professores')
@login_required
@perfil_requerido(PerfilEnum.ADMIN)
def professores():
    professores = Usuario.query.filter(Usuario.perfil == "PROFESSOR").all()
    return render_template('painel_professor.html', professores=professores)


@app.route('/devolver', methods=["GET", "POST"])
@login_required
@perfil_requerido(PerfilEnum.ADMIN)
def devolver():
    emprestimos = Emprestimo.query.filter_by(devolucao=False).all()
    return render_template('devolver_livro.html', emprestimos=emprestimos)


@app.route('/historico')
@login_required
def historico_aluno():
    emprestimos = Emprestimo.query.filter_by(
        usuario_id=current_user.id
    ).order_by(
        Emprestimo.data_emprestimo.desc()
    ).all()

    user = current_user.perfil
    hoje = date.today()

    return render_template(
        'historico_aluno.html',
        emprestimos=emprestimos,
        hoje=hoje,
        user=user
    )


@app.route('/devolver/<int:emprestimo_id>')
@login_required
@perfil_requerido(PerfilEnum.ADMIN)
def devolverid(emprestimo_id):
    emprestimo = Emprestimo.query.get_or_404(emprestimo_id)

    emprestimo.devolucao = True
    emprestimo.livro.disponiveis += 1

    db.session.commit()

    flash("Livro devolvido com sucesso!", "success")

    return redirect(url_for('devolver'))


@app.route('/relatorio')
@login_required
@perfil_requerido(PerfilEnum.ADMIN)
def relatorio():
    total_livros = Livro.query.count()
    emprestimo = Emprestimo.query.filter_by(devolucao=False)
    total_emprestimos = emprestimo.count()
    total_categorias = Categoria.query.count()

    return render_template(
        'relatorio.html',
        total_livros=total_livros,
        total_emprestimos=total_emprestimos,
        total_categorias=total_categorias,
        emprestimos=emprestimo
    )


@app.route("/categoria/nova", methods=["POST"])
@login_required
@perfil_requerido(PerfilEnum.ADMIN)
def nova_categoria():
    nome = request.form.get("nome")

    if nome:
        categoria = Categoria(nome=nome.capitalize())
        db.session.add(categoria)
        db.session.commit()

    return redirect(url_for("cadastrar_livro"))
