from flask import Flask, render_template, redirect, session, flash, request
from forms import Login, Registro, Send
from markupsafe import escape
import os
from utils import login_valido, pass_valido, email_valido
from werkzeug.security import check_password_hash, generate_password_hash
from db import accion, seleccion

app = Flask(__name__)

app.secret_key = os.urandom(24)


@app.route('/')
@app.route('/home/')
@app.route('/index/')
def inicio():
    frm=Login()
    return render_template('login.html', form=frm, titulo='Iniciar Sesión')

@app.route('/feed/')
def send():
    #frm = Send()
    return render_template('feed.html')
    #, form=frm, titulo='Enviar mensajes')

@app.route('/', methods=['POST'])
def login():
    frm=Login()
    usu = escape(frm.usu.data.strip())
    pwd = escape(frm.cla.data.strip())
    # Preparar la consulta
    sql = f"SELECT id, nombre, correo, clave FROM usuario WHERE usuario='{usu}'"
    # Ejecutar la consulta
    res = seleccion(sql)
    # Proceso los resultados
    if len(res)==0:
        flash('ERROR: Usuario o clave invalidos')
        return render_template('login.html', form=frm, titulo='Iniciar Sesión')
    else:
        cbd = res[0][3]  # Recuperar la clave
        if check_password_hash(cbd, pwd):
            session.clear()
            session['id'] = res[0][0]
            session['nom'] = res[0][1]
            session['usr'] = usu
            session['cla'] = pwd
            session['ema'] = res[0][2]
            return redirect('/message/')
        else:
            flash('ERROR: Usuario o clave invalidos')
            return render_template('login.html', form=frm, titulo='Iniciar Sesión')

@app.route('/message/')
def messages():
    usu = session['id']
    # Preparar la consulta
    sql = f"SELECT de, para, asunto, mensaje FROM mensajes WHERE para={usu}"
    # Ejecutar la consulta
    res = seleccion(sql)
    # Proceso los resultados
    if len(res)==0:
        tit = f"No hay mensajes registrados para {session['nom']}"
    else: 
        tit = f"Se muestran mensajes registrados para {session['nom']}"
    return render_template('mensajes.html', titulo=tit)

@app.route('/logout/')
def logout():
    session.clear()
    return redirect('/')

@app.route('/register/', methods=['GET', 'POST'])
def register():
    frm = Registro()
    if request.method == 'GET':
        return render_template('registro.html', form=frm, titulo='Registro de datos')
    else:
        # Recuperar los datos del formulario
        nom = escape(request.form['nom'])
        usu = escape(request.form['usu'])
        ema = escape(request.form['ema'])
        cla = escape(request.form['cla'])
        ver = escape(request.form['ver'])
        # Validar los datos
        swerror = False
        if nom==None or len(nom)==0:
            flash('ERROR: Debe suministrar un nombre de usuario')
            swerror = True
        if usu==None or len(usu)==0 or not login_valido(usu):
            flash('ERROR: Debe suministrar un usuario válido ')
            swerror = True
        if ema==None or len(ema)==0 or not email_valido(ema):
            flash('ERROR: Debe suministrar un email válido')
            swerror = True
        if cla==None or len(cla)==0 or not pass_valido(cla):
            flash('ERROR: Debe suministrar una clave válida')
            swerror = True
        if ver==None or len(ver)==0 or not pass_valido(ver):
            flash('ERROR: Debe suministrar una verificación de clave válida')
            swerror = True
        if cla!=ver:
            flash('ERROR: La clave y la verificación no coinciden')
            swerror = True
        if not swerror:
            # Preparar la consulta
            sql = 'INSERT INTO usuario(nombre, usuario, correo, clave) VALUES (?, ?, ?, ?)'
            # Ejecutar la consulta
            pwd = generate_password_hash(cla)  # Cifrar la clave
            res = accion(sql, (nom, usu, ema, pwd))
            # Verificar resultados
            if res==0:
                flash('ERROR: No se pudo insertar el registro')
            else:
                flash('INFO: Datos grabados con exito')
        return render_template('registro.html', form=frm, titulo='Registro de datos')

if __name__ == '__main__':
    app.run(debug=True, port=443)
    app.run( host='127.0.0.1', port=443 )





'''
cd env
cd scripts
activate.bat
set FLASK_APP=main
set FLASK_ENV=development
flask run
'''




