from datetime import datetime
from database import db


class Produto(db.Model):
    __tablename__ = 'produtos'

    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome        = db.Column(db.String(100), nullable=False)
    preco_venda = db.Column(db.Float, nullable=False)

    # Um produto pode aparecer em vários itens de comanda
    itens = db.relationship('ItemComanda', backref='produto', lazy=True)

    def __repr__(self):
        return f'<Produto {self.id} - {self.nome}>'


class Comanda(db.Model):
    __tablename__ = 'comandas'

    id                = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cliente           = db.Column(db.String(100), nullable=False)
    mesa              = db.Column(db.Integer, nullable=False)
    status            = db.Column(db.String(20), nullable=False, default='Aberta')
    horarioPedido     = db.Column(db.DateTime, nullable=False, default=datetime.now)
    horarioPagamento  = db.Column(db.DateTime, nullable=True)
    total             = db.Column(db.Float, nullable=False, default=0.0)
    observacao        = db.Column(db.String(300), nullable=True)

    # Uma comanda tem vários itens
    itens = db.relationship(
        'ItemComanda',
        backref='comanda',
        lazy=True,
        cascade='all, delete-orphan'   # apagar comanda apaga seus itens
    )

    def recalcular_total(self):
        """Recalcula e persiste o total com base nos itens atuais."""
        self.total = sum(item.subtotal for item in self.itens)

    def __repr__(self):
        return f'<Comanda {self.id} - {self.cliente} - Mesa {self.mesa}>'


class ItemComanda(db.Model):
    __tablename__ = 'itens_comanda'

    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    comanda_id     = db.Column(db.Integer, db.ForeignKey('comandas.id'), nullable=False)
    produto_id     = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=False)
    nome           = db.Column(db.String(100), nullable=False)   # snapshot do nome
    valor_unitario = db.Column(db.Float, nullable=False)          # snapshot do preço
    quantidade     = db.Column(db.Integer, nullable=False)
    subtotal       = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<ItemComanda comanda={self.comanda_id} produto={self.produto_id} qtd={self.quantidade}>'
