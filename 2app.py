import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

usuarios = []
mensagens = []

# Página inicial
@app.route("/")
def index():
    return render_template(
        "pages/index.html",
        total_usuarios=len(usuarios),
        total_mensagens=len(mensagens)
    )

# Usuários
@app.route("/usuarios", methods=["GET", "POST"])
def usuarios_view():
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")

        if not nome or not email:
            flash("Todos os campos são obrigatórios.", "danger")
            return redirect("/usuarios")

        # verificar duplicidade
        for u in usuarios:
            if u["email"] == email:
                flash("Email já cadastrado.", "danger")
                return redirect("/usuarios")

        usuarios.append({"nome": nome, "email": email, "qtd_mensagem":0,})
        flash("Usuário cadastrado com sucesso!", "success")

        return redirect("/usuarios")

    return render_template("pages/usuarios.html", usuarios=usuarios)

# Mensagens
@app.route("/mensagens", methods=["GET", "POST"])
def mensagens_view():
    if request.method == "POST":
        titulo = request.form.get("titulo")
        conteudo = request.form.get("conteudo")
        usuario_email = request.form.get("usuario_email")

        if not titulo or not conteudo:
            flash("Título e conteúdo são obrigatórios.", "danger")
            return redirect("/mensagens")

        mensagem = {
            "titulo": titulo,
            "conteudo": conteudo,
            "data_hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "usuario_email": usuario_email
        }

        for u in usuarios:
            if u["email"] == usuario_email:
                u["qtd_mensagem"]+=1
                
        mensagens.append(mensagem)
       
        mensagens.sort(key=lambda m: m["data_hora"], reverse=True)

        flash("Mensagem criada com sucesso!", "success")
        return redirect("/mensagens")

    return render_template(
        "pages/mensagens.html",
        mensagens=mensagens,
        usuarios=usuarios
    )

if __name__ == "__main__":
    app.run()