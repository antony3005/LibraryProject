from flask import render_template, request, redirect, url_for
from app import app, db
from app.models import Book, Loan


@app.route('/')
def home():
    return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        usuario = request.form.get('usuario')
        senha = request.form.get('senha')

        if usuario == 'abcd' and senha == '123':
            return redirect(url_for('menu'))

        return "Usuário ou senha inválidos"

    return render_template('login.html')


@app.route('/menu')
def menu():
    return render_template('menu.html')


@app.route('/acervo')
def acervo():
    livros = Book.query.all()
    return render_template('index.html', livros=livros)


@app.route('/cadastrar_livro', methods=['GET', 'POST'])
def cadastrar_livro():

    if request.method == 'POST':

        quantidade = int(request.form['quantidade'])

        livro = Book(
            isbn=request.form['isbn'],
            titulo=request.form['titulo'],
            autor=request.form['autor'],
            categoria=request.form['categoria'],
            editora=request.form['editora'],
            ano=request.form['ano'],
            quantidade=quantidade,
            disponiveis=quantidade
        )

        db.session.add(livro)
        db.session.commit()

        return redirect(url_for('acervo'))

    return render_template('cadastrar_livro.html')


@app.route('/editar_livro/<int:id>', methods=['GET', 'POST'])
def editar_livro(id):

    livro = Book.query.get_or_404(id)

    if request.method == 'POST':

        livro.isbn = request.form['isbn']
        livro.titulo = request.form['titulo']
        livro.autor = request.form['autor']
        livro.categoria = request.form['categoria']
        livro.editora = request.form['editora']
        livro.ano = request.form['ano']
        livro.quantidade = request.form['quantidade']

        db.session.commit()

        return redirect(url_for('acervo'))

    return render_template('editar_livro.html', livro=livro)


@app.route('/excluir_livro/<int:id>')
def excluir_livro(id):

    livro = Book.query.get_or_404(id)

    db.session.delete(livro)
    db.session.commit()

    return redirect(url_for('acervo'))


@app.route('/emprestimo', methods=['GET', 'POST'])
def emprestimo():

    livros = Book.query.all()

    if request.method == 'POST':

        usuario_id = request.form['usuario']
        livro_id = request.form['livro']

        livro = Book.query.get_or_404(livro_id)

        if livro.disponiveis is None:
            livro.disponiveis = livro.quantidade

        if livro.disponiveis <= 0:
            return "Não há exemplares disponíveis."

        novo_emprestimo = Loan(
            usuario_id=int(usuario_id),
            livro_id=int(livro_id)
        )

        livro.disponiveis -= 1

        db.session.add(novo_emprestimo)
        db.session.commit()

        return redirect(url_for('acervo'))

    return render_template(
        'emprestimo.html',
        livros=livros
    )


@app.route('/painel_aluno')
def painel_aluno():
    return render_template('painel_aluno.html')


@app.route('/painel_professor')
def painel_professor():
    return render_template('painel_professor.html')


@app.route('/relatorio')
def relatorio():
    return render_template('relatorio.html')