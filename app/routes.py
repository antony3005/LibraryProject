from functools import wraps

from flask import render_template, request, redirect, url_for, abort
from flask_login import current_user, login_user, login_required, logout_user
from sqlalchemy import or_

from app import app, db
from app.form import CadastroUsuario, CadastroLivro, EditarLivro, LoginForm
from app.models import Livro, Emprestimo, Usuario, PerfilEnum


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

    # Busca por título, autor ou editora
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

        livro = Livro.query.get_or_404(livro_id)

        if livro.disponiveis is None:
            livro.disponiveis = livro.quantidade

        if livro.disponiveis <= 0:
            return "Não há exemplares disponíveis."

        novo_emprestimo = Emprestimo(
            usuario_id=int(usuario_id),
            livro_id=int(livro_id)
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

    return render_template('cadastrar_livro.html', form=form)


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

        perfil = form.perfil.data
        senha = form.senha.data

        if perfil == "admin":
            if not senha:
                return "Admin precisa de senha!", 400

        user = Usuario(
            nome=form.nome.data,
            sobrenome=form.sobrenome.data,
            email=form.email.data,
            perfil=PerfilEnum(form.perfil.data)
        )

        user.set_password(form.senha.data)

        db.session.add(user)
        db.session.commit()

        return f"Criado: {perfil}"

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


@app.route('/relatorio')
@login_required
@perfil_requerido(PerfilEnum.ADMIN)
def relatorio():
    return render_template('relatorio.html')
