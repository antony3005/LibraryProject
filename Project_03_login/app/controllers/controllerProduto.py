from app.models import Produto, Categoria
from app        import db

class ControllerProduto():
    @staticmethod
    def registerNewProduct(product: Produto):
        db.session.add(product)
        db.session.commit()
    
    @staticmethod
    def product_order_by_name():
        return Produto.query.order_by(Produto.name).all()

    @staticmethod
    def product_order_by_price():
        return Produto.query.order_by(Produto.price).all()
    
    @staticmethod
    def product_get_by_id(id):
        return Produto.query.get_or_404(id)
    
    @staticmethod
    def saveProductEdited(form, product: Produto):
        form.populate_obj(product)
        db.session.commit()

    @staticmethod
    def deleteProduct(id: int):
        product      = Produto.query.get_or_404(id)
        nome_produto = product.name
        db.session.delete(product)
        db.session.commit()
        return nome_produto