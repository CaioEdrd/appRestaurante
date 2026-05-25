from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime

from database import init_db, db, migrate
from models import Produto, Comanda, ItemComanda


app = Flask(__name__)
app.secret_key = "123456"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///banco.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


init_db(app)
migrate.init_app(app,db)


# ─────────────────────────────────────────────
#  COMANDAS
# ─────────────────────────────────────────────

@app.route('/', methods=["GET", "POST"])
def comandas():
    dataHoje = datetime.now()

    if request.method == "POST":
        mesa = request.form.get("mesa")
        cliente = request.form.get("cliente")
        observacao = request.form.get("observacao")

        if not cliente:
            flash("É necessário colocar o nome do cliente", "danger")
            return redirect(url_for("comandas"))

        if not mesa:
            flash("É necessário colocar a mesa do cliente", "danger")
            return redirect(url_for("comandas"))

        # Verifica mesa com comanda aberta
        mesa_ocupada = Comanda.query.filter_by(mesa=int(mesa), status="Aberta").first()
        if mesa_ocupada:
            flash("Mesa com comanda aberta!", "danger")
            return redirect(url_for("comandas"))

        # Monta itens do pedido
        produtos = Produto.query.all()
        itens = []
        total = 0.0

        for produto in produtos:
            quantidade = request.form.get(f'quantidade_{produto.id}')
            quantidade = int(quantidade) if quantidade else 0

            if quantidade > 0:
                subtotal = quantidade * produto.preco_venda
                itens.append(ItemComanda(
                    produto_id=produto.id,
                    nome=produto.nome,
                    valor_unitario=produto.preco_venda,
                    quantidade=quantidade,
                    subtotal=subtotal,
                ))
                total += subtotal

        if total == 0:
            flash("Não há itens na comanda", "danger")
            return redirect(url_for("comandas"))

        comanda = Comanda(
            cliente=cliente,
            mesa=int(mesa),
            observacao=observacao,
            total=total,
        )
        db.session.add(comanda)
        db.session.flush()   # garante comanda.id antes de associar itens

        for item in itens:
            item.comanda_id = comanda.id
            db.session.add(item)

        db.session.commit()
        flash("Comanda aberta com sucesso!", "success")
        return redirect(url_for("comandas"))

    # ── KPIs ──────────────────────────────────
    todas = Comanda.query.order_by(Comanda.id).all()
    produtos = Produto.query.all()

    total_abertas       = Comanda.query.filter_by(status="Aberta").count()
    total_pagas         = Comanda.query.filter_by(status="Paga").count()
    total_inadimplentes = Comanda.query.filter_by(status="Inadimplente").count()
    total_comandas      = Comanda.query.count()

    faturamento = db.session.query(
        db.func.coalesce(db.func.sum(Comanda.total), 0)
    ).scalar()

    ultimosCinco = Comanda.query.order_by(Comanda.id.desc()).limit(5).all()

    return render_template(
        'comandas.html',
        listaComandas=todas,
        ultimosCinco=ultimosCinco,
        total_abertas=total_abertas,
        total_pagas=total_pagas,
        total_inadimplentes=total_inadimplentes,
        total_comandas=total_comandas,
        dataHoje=dataHoje,
        produtos=produtos,
        faturamento=faturamento,
    )


@app.route('/comanda/<int:id>', methods=["GET", "POST"])
def detalhe_comanda(id):
    comanda = Comanda.query.get_or_404(id)

    # Calcula tempo da comanda
    fim = comanda.horarioPagamento if comanda.horarioPagamento else datetime.now()
    tempo_aberta = str(fim - comanda.horarioPedido).split(".")[0]

    if request.method == "POST":
        produtos = Produto.query.all()
        adicionou_algum = False

        for produto in produtos:
            quantidade = request.form.get(f'quantidade_{produto.id}')
            quantidade = int(quantidade) if quantidade else 0

            if quantidade > 0:
                item_existente = ItemComanda.query.filter_by(
                    comanda_id=comanda.id,
                    produto_id=produto.id
                ).first()

                if item_existente:
                    item_existente.quantidade += quantidade
                    item_existente.subtotal = (
                        item_existente.quantidade * item_existente.valor_unitario
                    )
                else:
                    novo_item = ItemComanda(
                        comanda_id=comanda.id,
                        produto_id=produto.id,
                        nome=produto.nome,
                        valor_unitario=produto.preco_venda,
                        quantidade=quantidade,
                        subtotal=quantidade * produto.preco_venda,
                    )
                    db.session.add(novo_item)

                adicionou_algum = True

        if adicionou_algum:
            db.session.flush()
            comanda.recalcular_total()
            db.session.commit()
            flash("Itens adicionados com sucesso!", "success")
        else:
            flash("Nenhum item selecionado", "warning")

        return redirect(url_for('detalhe_comanda', id=id))

    produtos = Produto.query.all()
    return render_template(
        'comanda_detalhe.html',
        comanda=comanda,
        tempo_aberta=tempo_aberta,
        produtos=produtos,
    )


@app.route('/comanda/<int:id>/editar', methods=["GET", "POST"])
def editar_comanda(id):
    comanda = Comanda.query.get_or_404(id)

    if request.method == "POST":
        comanda.cliente = request.form.get('cliente')
        comanda.mesa = int(request.form.get('mesa'))

        if comanda.status == "Aberta":
            novo_status = request.form.get('status')
            comanda.status = novo_status

        if comanda.status in ("Paga", "Inadimplente"):
            if not comanda.horarioPagamento:
                comanda.horarioPagamento = datetime.now()

        db.session.commit()
        flash("Comanda editada com sucesso!", "success")
        return redirect(url_for('comandas'))

    return render_template('comanda_editar.html', comanda=comanda)


@app.route('/comanda/<int:id>/apagar')
def apagar_comanda(id):
    comanda = Comanda.query.get_or_404(id)
    db.session.delete(comanda)
    db.session.commit()
    flash("Comanda apagada com sucesso!", "success")
    return redirect(url_for('comandas'))


# ─────────────────────────────────────────────
#  ITENS DA COMANDA
# ─────────────────────────────────────────────

@app.route('/comanda/<int:comanda_id>/item/<int:item_id>/editar', methods=['GET', 'POST'])
def editar_item(comanda_id, item_id):
    comanda = Comanda.query.get_or_404(comanda_id)
    item    = ItemComanda.query.get_or_404(item_id)

    if request.method == "POST":
        quantidade = int(request.form.get("quantidade"))
        item.quantidade = quantidade
        item.subtotal   = quantidade * item.valor_unitario
        comanda.recalcular_total()
        db.session.commit()
        flash("Item atualizado com sucesso!", "success")
        return redirect(url_for('detalhe_comanda', id=comanda_id))

    return render_template('item_editar.html', comanda=comanda, item=item)


@app.route('/comanda/<int:comanda_id>/item/<int:item_id>/apagar')
def apagar_item(comanda_id, item_id):
    comanda = Comanda.query.get_or_404(comanda_id)
    item    = ItemComanda.query.get_or_404(item_id)

    db.session.delete(item)
    db.session.flush()
    comanda.recalcular_total()
    db.session.commit()
    flash("Item apagado com sucesso!", "success")
    return redirect(url_for('detalhe_comanda', id=comanda_id))


# ─────────────────────────────────────────────
#  PRODUTOS
# ─────────────────────────────────────────────

@app.route('/produtos')
def produto():
    produtos = Produto.query.all()
    return render_template('produtos.html', produtos=produtos)


@app.route('/produtos/cadastrar', methods=['POST'])
def cadastrar_produto():
    nome  = request.form['nome']
    preco = float(request.form['preco_venda'])

    produto = Produto(nome=nome, preco_venda=preco)
    db.session.add(produto)
    db.session.commit()
    return redirect(url_for('produto'))


@app.route('/produtos/<int:id>/editar', methods=['GET'])
def editar_produto(id):
    produto = Produto.query.get_or_404(id)
    return render_template('produto_editar.html', produto=produto)


@app.route('/produtos/<int:id>/atualizar', methods=['POST'])
def atualizar_produto(id):
    produto = Produto.query.get_or_404(id)
    produto.nome        = request.form['nome']
    produto.preco_venda = float(request.form['preco_venda'])
    db.session.commit()
    return redirect(url_for('produto'))


@app.route('/produtos/<int:id>/apagar')
def apagar_produto(id):
    produto = Produto.query.get_or_404(id)
    db.session.delete(produto)
    db.session.commit()
    return redirect(url_for('produto'))


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
