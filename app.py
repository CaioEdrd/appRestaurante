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
    ultimosCinco =[]
    dataHoje = datetime.now()

    total_comandas = len(listaComandas)
    total_abertas = len(comandas_abertas)
    total_fechadas = len(comandas_fechadas) 

    if request.method == "POST":
        comanda_id=1

        for p in produtos:        
            pedido={
                "item" : p.nome,
                "valor": p.preco_venda,
                "quantidade": request.form.get("produto_quantidade")
            }

            
            comanda = {
                "id" : comanda_id,
                "cliente": request.form.get("cliente"),
                "mesa": request.form.get("mesa"),
                "horarioPedido":datetime.now(),
                "status": "Aberta",
                "total": 0,
            }
            
            for u in listaComandas:
                if u["mesa"] == comanda.mesa and u["status"] == "Aberta":
                    flash("Mesa com comanda aberta!", "danger")
                    break
                else:
                    comanda_id +=1
                    listaComandas.append(comanda)
                    flash("Comanda aberta com sucesso!", "success")

    if total_comandas > 0:

        for u in listaComandas:
            if u["status"] =="Aberta":
                comandas_abertas.append(u)

        for f in listaComandas:
            if f["status"] =="Fechada":
                comandas_fechadas.append(f) 
             
        ultimosCinco = listaComandas[-5:][::-1]

    return render_template('comandas.html', listaComandas=listaComandas, ultimosCinco=ultimosCinco, total_abertas=total_abertas, total_fechadas=total_fechadas, total_comandas=total_comandas, dataHoje=dataHoje, produtos=produtos)


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