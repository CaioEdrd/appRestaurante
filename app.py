from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import os



app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

produtos = []
listaComandas=[]
contador_id = 1

@app.route('/', methods = ["GET", "POST"])
def comandas():
    comandas_abertas = []
    comandas_fechadas = []
    ultimosCinco = []
    faturamento = 0

    dataHoje = datetime.now()

    if request.method == "POST":

        pedido = []

        total = 0

        comanda_id = len(listaComandas) + 1

        for c in listaComandas:

            if (
                str(c["mesa"]) == request.form.get("mesa")
                and
                c["status"] == "Aberta"
            ):

                flash("Mesa com comanda aberta!", "danger")

                return redirect(url_for("comandas"))
        
        for produto in produtos:

            quantidade = request.form.get(
                f'quantidade_{produto["id"]}'
            )

            quantidade = int(quantidade)

            if quantidade > 0:
                subtotal = (quantidade *float(produto["preco_venda"]) )

                item = {
                    "produto_id": produto["id"],
                    "nome": produto["nome"],
                    "valor_unitario": produto["preco_venda"],
                    "quantidade": int(quantidade),
                    "subtotal": float(subtotal)}

                pedido.append(item)
                total += subtotal

        comanda = {
            "id": comanda_id,
            "cliente": request.form.get("cliente"),
            "mesa": request.form.get("mesa"),
            "horarioPedido": datetime.now(),
            "horarioPagamento": "-",
            "status": "Aberta",
            "pedido": pedido,
            "total": float(total),
            "observacao": request.form.get("observacao"),
        }

        if comanda["cliente"] == "":
            flash("É necessário colocar o nome do cliente", "danger")
            return redirect(url_for("comandas"))

        if comanda["mesa"] == "":
            flash("É necessário colocar a mesa do cliente", "danger")
            return redirect(url_for("comandas"))

        if total > 0:
            listaComandas.append(comanda)

            flash("Comanda aberta com sucesso!", "success")

            return redirect(url_for("comandas"))
        else:
            flash("Não há itens na comanda", "danger")
            return redirect(url_for("comandas"))


    # KPIs
    total_comandas = len(listaComandas)

    for c in listaComandas:

        if c["status"] == "Aberta":
            comandas_abertas.append(c)

        elif c["status"] == "Fechada":
            comandas_fechadas.append(c)

    total_abertas = len(comandas_abertas)

    total_fechadas = len(comandas_fechadas)

    ultimosCinco = listaComandas[-5:][::-1]
    
    for c in listaComandas:
        faturamento += c["total"]

    return render_template( 'comandas.html', listaComandas=listaComandas,  ultimosCinco=ultimosCinco,total_abertas=total_abertas, total_fechadas=total_fechadas, total_comandas=total_comandas, dataHoje=dataHoje, produtos=produtos, faturamento=faturamento)

@app.route('/comanda/<int:id>', methods = ["GET", "POST"])
def detalhe_comanda(id):
    tempo_aberta = datetime.now()
    comanda = None
    for i in listaComandas:
        if i["id"] == id:
            comanda = i  # Encontrou a comanda!
            if comanda["horarioPagamento"] == "-":
                diferenca = datetime.now() - comanda["horarioPedido"]
                tempo_str = str(diferenca)
                tempo_aberta = tempo_str.split(".")[0]
            else:
                diferenca = comanda["horarioPagamento"] - comanda["horarioPedido"]
                tempo_str = str(diferenca)
                tempo_aberta = tempo_str.split(".")[0]
            break    

    if request.method=="POST":
        for produto in produtos:
            quantidade = request.form.get(
                f'quantidade_{produto["id"]}'
            ) 
            
            quantidade = int(quantidade) or 0

            if quantidade > 0:
                subtotal = (quantidade *float(produto["preco_venda"]) )

                item = {
                        "produto_id": produto["id"],
                        "nome": produto["nome"],
                        "valor_unitario": float(produto["preco_venda"]),
                        "quantidade": int(quantidade),
                        "subtotal":float(subtotal)}
                
                produto_existe = False

                for i in comanda["pedido"]:
                    if i["nome"] == item["nome"]:
                        # INCREMENTA QUANTIDADE
                        i["quantidade"] += item["quantidade"]

                        # RECALCULA SUBTOTAL
                        i["subtotal"] = (
                            int(i["quantidade"]) *
                            float(i["valor_unitario"])
                        )

                        produto_existe = True

                        flash(
                            "Quantidade atualizada com sucesso!",
                            "success"
                        )

                        break


                if not produto_existe:

                    comanda["pedido"].append(item)

                    flash(
                        "Item adicionado com sucesso!",
                        "success"
                    )

                comanda["total"] = sum(
                    float(item["subtotal"])
                    for item in comanda["pedido"]
                )

                return redirect(
                    url_for('detalhe_comanda', id=id)
                )
    return render_template('comanda_detalhe.html', comanda = comanda, tempo_aberta=tempo_aberta, produtos=produtos)

@app.route('/comanda/<int:id>/editar', methods = ["GET", "POST"])
def editar_comanda(id):
    comanda = next((i for i in listaComandas if i['id'] == id), None)
    if request.method == "POST":
        if comanda is not None:
            comanda['cliente'] = request.form.get('cliente')
            comanda['mesa'] = request.form.get('mesa')
            if comanda['status'] != "Fechada":
                comanda['status'] = request.form.get('status')
            else:
                comanda['status'] = "Fechada"
            if comanda['status'] != "Aberta":
                comanda['horarioPagamento'] = datetime.now()
        flash("Comanda Editada com Sucesso", "success")
        
        return redirect(url_for('comandas'))

    return render_template('comanda_editar.html', listaComandas=listaComandas, comanda=comanda)

@app.route('/comanda/<int:id>/apagar')
def apagar_comanda(id):
    global listaComandas
    listaComandas = [c for c in listaComandas if c['id'] != id]
    return redirect(url_for('comandas'))

@app.route('/comanda/<int:id>/cancelar', methods = ["GET", "POST"])
def cancelar_comanda(id):
    comanda = next((i for i in listaComandas if i['id'] == id), None)

    comanda['status'] = "Cancelada"
    comanda['horarioPagamento'] = datetime.now()
    
    return redirect(url_for("comandas"))

@app.route('/comanda/<int:comanda_id>/item/<int:produto_id>/editar', methods=['GET', 'POST'])
def editar_item(comanda_id, produto_id):
    comanda = next(
        (c for c in listaComandas if c["id"] == comanda_id),
        None)

    if comanda is None:
        return "Comanda não encontrada"

    item = next(
        (i for i in comanda["pedido"]
         if i["produto_id"] == produto_id),
        None)

    if item is None:
        return "Item não encontrado"

    if request.method == "POST":

        quantidade = int(request.form.get("quantidade"))

        item["quantidade"] = quantidade

        item["subtotal"] = (
            quantidade *
            float(item["valor_unitario"]))

        comanda["total"] = sum(
            i["subtotal"]
            for i in comanda["pedido"])

        flash("Item atualizado com sucesso!", "success")

        return redirect(
            url_for(
                'detalhe_comanda',
                id=comanda_id)
        )

    return render_template(
        'item_editar.html',
        comanda=comanda,
        item=item
    )
@app.route(
    '/comanda/<int:comanda_id>/item/<int:produto_id>/apagar'
)
def apagar_item(comanda_id, produto_id):
    comanda = next(
        (c for c in listaComandas if c["id"] == comanda_id),
        None)

    if comanda is None:
        return "Comanda não encontrada"

    comanda["pedido"] = [
        i for i in comanda["pedido"]
        if i["produto_id"] != produto_id]

    comanda["total"] = sum(
        i["subtotal"]
        for i in comanda["pedido"])

    flash("Item apagado com sucesso!", "success")

    return redirect(
        url_for(
            'detalhe_comanda',
            id=comanda_id)
    )

@app.route('/produto')
def produto():
    return render_template('produtos.html', produtos=produtos)

@app.route('/cadastrar', methods=['POST'])
def cadastrar_produto():
    global contador_id

    nome = request.form['nome']
    preco = request.form['preco_venda']

    produto = {
        'id': contador_id,
        'nome': nome,
        'preco_venda': preco
    }
    produtos.append(produto)
    contador_id += 1

    return redirect(url_for('produto'))

@app.route('/editar_produto/<int:id>')
def editar_produto(id):
    produto = next((i for i in produtos if i['id'] == id), None)

    if produto is None:
        return "Produto não encontrado"
    
    return render_template('produto_editar.html', produto=produto)

@app.route('/atualizar_produto/<int:id>', methods=['POST'])
def atualizar_produto(id):
    produto = next((i for i in produtos if i['id'] == id), None)

    if produto is not None:
        produto['nome'] = request.form['nome']
        produto['preco_venda'] = request.form['preco_venda']

    return redirect(url_for('produto'))

@app.route('/apagar/<int:id>')
def apagar_produto(id):
    global produtos

    produtos = [p for p in produtos if p['id'] != id]
    return redirect(url_for('produto'))


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)