from app         import app
from flask       import Flask, render_template, redirect, url_for, request, flash
from datetime    import datetime
from typing      import Final
from app.models  import db, Produto, Categoria
from app.forms   import ProdutoForm, UserForm, LoginForm
from sqlalchemy  import func
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from app.controllers.controllerProduto import ControllerProduto
from app.controllers.controllerUser     import ControllerUser

PAGE_PRODUCT_LIST:     Final[str] = "productList.html"
PAGE_PRODUCT_REGISTER: Final[str] = "productRegister.html"
PAGE_USER_REGISTER:    Final[str] = "userRegister.html"
PAGE_PRODUCT_INFO:     Final[str] = "productDetails.html"
PAGE_REPORTER:         Final[str] = "reporter.html"
HOME_PAGE:             Final[str] = "index.html"  


def checkForm(form):
    if request.method == 'POST':
        form.validate()
        if form.errors:
            for msg in form.errors.values():
                flash(msg[0], 'danger')


@app.route('/', methods = ['GET', 'POST'])
def index():
    if ControllerUser.isLoged():
        return render_template(HOME_PAGE)
    # Se não estiver logado, processa o formulário de login
    form = LoginForm()
    if form.validate_on_submit():
        user = form.login()
        if user:
            login_user(user)
            flash('Login realizado com sucesso', 'success')
            return redirect(url_for('index'))
        else:
            flash('Email ou senha incorretos', 'danger')
    return render_template(HOME_PAGE, form = form)

@app.route('/user/sair')
def logout():
    logout_user()
    flash('Você saiu do sistema.', 'success')
    return redirect(url_for('index'))

@app.route('/user/cadastro', methods = ['GET', 'POST'])
@login_required
def cadastrar_usuario():
    if ControllerUser.checkAdminPermission():
        form = UserForm()
        # Verifica se o formulário está sem errors.
        checkForm(form)
        if form.validate_on_submit():
            user = form.saveUser()
            flash('Usuário cadastrado com sucesso!', 'success')
            return redirect(url_for('index'))
        return render_template(PAGE_USER_REGISTER, form = form)
    else:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('index'))

# Rota de Cadastro de produtos
@app.route('/produto/novo', methods = ['GET', 'POST'])
@login_required
def cadastrar_produto():
    form = ProdutoForm()
    # Carrega as categorias dinamicamente no SelectField
    form.categoria_id.choices = [(c.id, c.name) for c in Categoria.query.order_by('name').all()]
    checkForm(form)
    if form.validate_on_submit():
        form.saveData()
        flash('Produto cadastrado com sucesso!', 'success')
        return redirect(url_for('listar_produtos'))
    return render_template(PAGE_PRODUCT_REGISTER, form = form)

# Rota de Listagem Ordenada
@app.route('/produtos')
def listar_produtos():
    orderProduct_by = request.args.get('ordem', 'nome') # Valor default: 'nome'
    if orderProduct_by == 'preco':
        produtos = ControllerProduto.product_order_by_price()
    else:
        produtos = ControllerProduto.product_order_by_name()
        
    return render_template(PAGE_PRODUCT_LIST, produtos = produtos, ordem_atual = orderProduct_by)

# Visualização (Rota Dinâmica)
@app.route('/produto/<int:id>')
def visualizar_produto(id):
    product = ControllerProduto.product_get_by_id(id)
    return render_template(PAGE_PRODUCT_INFO, produto = product)

@app.route('/produto/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_produto(id):
    product = ControllerProduto.product_get_by_id(id)
    # Instancia o formulário passando o objeto 'produto' para preencher os campos automaticamente
    form = ProdutoForm(obj = product)
    form.categoria_id.choices = [(c.id, c.name) for c in Categoria.query.order_by('name').all()]
    checkForm(form)
    if form.validate_on_submit():
        ControllerProduto.saveProductEdited(form, product)
        flash(f'Produto "{product.name}" atualizado com sucesso!', 'success')
        return redirect(url_for('listar_produtos'))
        
    return render_template(PAGE_PRODUCT_REGISTER, form = form, editando = True)

@app.route('/produto/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_produto(id):
    if ControllerUser.checkAdminPermission():
        flash(f'Produto "{ControllerProduto.deleteProduct(id)}" excluído com sucesso!', 'success')
        return redirect(url_for('listar_produtos'))
    else:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('index'))

@app.route('/categorias/relatorio')
@login_required
def relatorio_categorias():
    if ControllerUser.checkAdminPermission():
        # Consulta equivalente ao SQL: 
        # SELECT categorias.name, COUNT(produtos.id) FROM categorias 
        # LEFT JOIN produtos ON categorias.id = produtos.categoria_id GROUP BY categorias.id;
        relatorio = db.session.query(
            Categoria.name.label('categoria_nome'),
            func.count(Produto.id).label('total_produtos')
        ).outerjoin(Produto).group_by(Categoria.id).all()
        
        return render_template(PAGE_REPORTER, reporter = relatorio)
    else:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('index'))