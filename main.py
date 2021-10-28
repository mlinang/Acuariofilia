import os
from flask.helpers import flash
from werkzeug.utils import secure_filename
from flask import flash, sessions
from markupsafe import escape
from forms.forms import *
from flask import Flask, render_template, url_for, redirect, jsonify, request, session
from db import *
from utils import isUsernameValid, isEmailValid, isPasswordValid
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import functools

UPLOAD_FOLDER = os.path.abspath("static/images/Post")
ALLOWED_EXTENSIONS = set(["png","jpg", "jpeg"])

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/') 
@app.route('/feed')
#@login_required
def feed():
    #@pablo@ esta condicion es por si alguien escribe directamente /feed en el navegador y no se encuentra logeado lo manda al login
    #probando esto me di cuenta que le doy logout me manda al login, pero si escribo /feed puedo abrirlo porque no ha salido de la sesion. 
    if 'fullname' in session:
        usu= session['id']
        sql ="SELECT * FROM Post order by creationDate desc limit 10"
        posts = selectSQLite(sql)
        sql =f'SELECT * FROM Post WHERE UserId = {usu} order by creationDate desc limit 20'
        postown = selectSQLite(sql)
        """ return render_template("feed.html", posts=posts, postown=postown) """
        #@pablo@ active la condicion para que si no tiene una sesion abierta lo envie al login.
        if 'fullname' in session and (session['rol'] == 1 or session['rol'] ==2) :
            sql ="SELECT * FROM Post"
            posts = selectSQLite(sql)
            return render_template("feed.html", posts=posts, postown=postown)
        
        else:
            return redirect('login')
        
    else:
        return redirect('login')

@app.route('/addPost', methods=['GET', 'POST'])
def addPost():
    form = Postform()
    if request.method == 'POST':
        nombre = request.form['nombre']
        imagen = request.files['imagen']
        filename = secure_filename(imagen.filename)
        imagen.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))     
        db = get_db()
        db.execute('INSERT INTO Post (PhotoURL,Title, creationDate, UserId) VALUES(?,?,?,?)', (filename,nombre, datetime.now(), session['id']))
        db.commit()
        mensajeExitoso ="Registro exitoso"
        return redirect(url_for('feed', mensajeExitoso=mensajeExitoso))
    return render_template('addPost.html', form=form)
       
@app.route('/deleteComm', methods=['GET', 'POST'])
def deleteComm():
    msg='Post eliminado exitosamente'
    id = request.args.get('codigo')
    postId=request.args.get('postId')
    sql = f'DELETE FROM Comments WHERE CommentId = {id}'
    updateSQLite(sql,"cerrar")
    flash(msg)
    return redirect(url_for('postdetail', codigo=postId))

@app.route('/deletePost', methods=['GET', 'POST'])
def deletePost():
    msg='Post eliminado exitosamente'
    postId=request.args.get('codigo')
    sql = f'DELETE FROM Post WHERE PostId = {postId}'
    updateSQLite(sql,"nada")
    sql = f'DELETE FROM Comments WHERE PostId = {postId}'
    updateSQLite(sql,"cerrar")
    flash(msg)
    return redirect(url_for('feed'))

@app.route('/deleteUser', methods=['GET', 'POST'])
def deleteUser():
    msg='Usuario eliminado exitosamente'
    userId = request.args.get('userId')
    sql = f'DELETE FROM User WHERE UserId = {userId}'
    updateSQLite(sql,"nada")
    sql = f'DELETE FROM Post WHERE UserId = {userId}'
    updateSQLite(sql,"nada")
    sql = f'DELETE FROM Comments WHERE UserId = {userId}'
    updateSQLite(sql,"cerrar")
    flash(msg)
    return redirect( url_for('search', codigo=userId) )

@app.route('/postdetail')
def postdetail():
    idp = request.args.get('codigo')
    sql = f'SELECT * FROM Post , User WHERE User.UserId=Post.UserId AND Post.PostId = {idp}'
    postsel= selectSQLite(sql)
    sql = f'SELECT * from Comments, User WHERE User.UserId=Comments.UserId AND Comments.PostId = {idp}'
    comPost= selectSQLite(sql)
    return render_template("postdetail.html", postsel=postsel,comPost=comPost)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ""
    form = LoginForm()
    if(form.validate_on_submit()):                
        email = escape(form.email.data.strip())
        password = escape(form.password.data.strip())
        sql = f'SELECT * FROM User WHERE email = "{email}"'       
        usuarios =selectSQLite(sql)
        if len(usuarios) > 0:
            contrasenaHas = usuarios[0][4]
            if check_password_hash(contrasenaHas, password):            
                session.clear()
                session['id'] = usuarios[0][0]
                session['fullname'] = usuarios[0][1] + " " + usuarios[0][2]
                session['correo'] = usuarios[0][3]
                session['rol'] = usuarios[0][7]
                session['password'] = contrasenaHas
                session['foto'] = usuarios[0][9]
                if session['rol'] == 2:
                    return redirect(url_for('feed'))                                
                else:
                    return redirect(url_for('dashboard'))
            else:
                flash(f'Usuario y/o Clave incorrecta')
                return redirect(url_for('login'))
        else:
                flash(f'Usuario y/o Clave incorrecta')             
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    if 'id' in session:
        session.clear()
    return redirect(url_for('feed'))

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    form = UserForm()
    if request.method == 'POST':
        nombre = request.form['firstname']
        apellido = request.form['lastname']            
        email = request.form['email']
        password = request.form['password']
        birthday = request.form['Birthdate']
        gender="Masculino"
        role=2
        CreationDate= datetime.now()
        
        #Si el correo es valido, si el correo existe, si el password es valido
        sql = f'SELECT * FROM User WHERE email = "{email}"'   
        usuarios = selectSQLite(sql)
        error = None
        if len(usuarios) > 0:  #si ya existe un usuario con ese email
            error = "El correo ingresado ya se encuentra en uso"
            flash(error)
        if not isEmailValid(email):
            error = "El correo ingresado es inválido"
            flash(error)
        if not isPasswordValid(password):
            error = "La contraseña debe tener entre 8 y 16 caracteres, al menos un dígito, al menos una minúscula y al menos una mayúscula, sin caracteres especiales."
            flash(error)
        if error is not None:
            # Ocurrió un error
            print(error)
            return render_template("registro.html", form=form)
        else:
            contrasenaHas = generate_password_hash(password)
            sql = 'INSERT INTO User (name,Lastname,email,password,gender,birthay,role,CreationDate) VALUES (?,?,?,?,?,?,?,?) '  
            db = get_db()
            result = db.execute(sql, (nombre,apellido,email,contrasenaHas,gender,birthday,role,CreationDate)).rowcount
            db.commit()
            if result!=0:
                flash('Registro exitoso')
            else:
                flash('Woops! Hubo un error. Intenta nuevamente')
    return render_template('registro.html', form=form)

@app.route('/cambiarcontrasena', methods=['GET', 'POST']) #ojo... debe haber siempre una sesion activa
def changepass():
    error1 = None
    form = UserForm()
    if request.method == 'POST':
        currentPass = request.form['password']
        newPass1 = request.form['newPass1']            
        newPass2 = request.form['newPass2']

        if not check_password_hash(session['password'], currentPass):    #si la clave hash de la sesion activa no coincide con la ingresada
            error1 = "Error al validar la contraseña actual"   #ojo, si no hay sesión activa da error
            flash(error1)
        if newPass1 != newPass2:    #si los dos campos de nueva contraseña no coinciden
            error1 = "Error al validar la nueva contraseña"
            flash(error1)
        if not isPasswordValid(newPass1):
            error1= "La contraseña debe tener entre 8 y 16 caracteres, al menos un dígito, al menos una minúscula y al menos una mayúscula, sin caracteres especiales."
            flash(error1)
        else:
            newPassHash = generate_password_hash(newPass1)  #genera nueva contraseña encriptada
        if error1 is not None:
            print(error1)
            return render_template("cambiarcontrasena.html", form=form)

        else:
            db = get_db()
            sql1 = f'UPDATE User SET password = ? WHERE email = ?'
            result = db.execute(sql1, (newPassHash, session['correo'])).rowcount
            db.commit()  
            if result > 0:
                flash('Se actualizó la contraseña exitosamente')
            else:
                flash('No se pudo actualizar la contraseña')
    return render_template("cambiarcontrasena.html", form=form)

@app.route('/makeAdmin', methods=['GET', 'POST']) #ojo... debe haber siempre una sesion activa
def makeAdmin():
    userId = request.args.get('userId')
    sql = f'UPDATE User SET role = 1 WHERE UserId = {userId}' #rol 1: admin, al usuario del post seleccionado
    updateSQLite(sql, "cerrar")
    flash('Se han otorgado privilegios de administrador al usuario de forma exitosa')
    return redirect(url_for('perfil', codigo=userId))

@app.route('/restablecercontrasena')
def restablecercontrasena():
    return render_template("restablecercontrasena.html") 

@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html")      

@app.route('/search', methods=['GET', 'POST'])
def search():
    form = searchForm()
    if request.method == 'POST':
        clave = request.form['palabra']
        sql = f'SELECT UserId,name, lastname, email,birthay,gender,CreationDate,ProfilePicURL FROM User WHERE name LIKE "%{clave}%" OR lastname LIKE "%{clave}%"'   
        Sresult = selectSQLite(sql)
        sql = f'SELECT * FROM Post WHERE title LIKE "%{clave}%"'    
        posts = selectSQLite(sql)
        if len(Sresult) or len(posts) > 0:
            return render_template("search.html", Sresult=Sresult, posts=posts)                               
        else:
            flash(f'La busqueda no arrojo resultados')
            return redirect(url_for('feed'))
    if request.method == 'GET':
        return render_template("search.html")

@app.route('/perfil')
def perfil():
    form = UserForm()
    if request.method == 'GET':
        idsel = request.args.get('codigo')
        sql = f'SELECT * FROM User WHERE UserId = {idsel}'
        psel = selectSQLite(sql)
        return render_template("perfil.html", psel=psel[0])
   
@app.route('/addcomm', methods=['GET','POST'])
def addcomm():
    postsel = request.args.get('codigo') #recupera el valor de la variable codigo enviada por GET
    contenido = request.form['comentario']
    id=session['id']
    time= datetime.now()
    if request.method == 'POST':
        sql=(f'INSERT INTO Comments (Content, PostId, UserId, CreationDate) VALUES({contenido},{postsel},{id},{time})')
        updateSQLite(sql, "cerrar")
        
    return redirect(url_for('postdetail', codigo=postsel))


def updateSQLite(sql, accion): #accion es para indicar que se puede cerrar la instancia de la base de datos.
    db = get_db()
    db.execute(sql)
    db.commit()
    if  accion=="cerrar":
        db.close()

def selectSQLite(sql):
    db = get_db()
    cursorObj = db.cursor()
    cursorObj.execute(sql)
    seleccion = cursorObj.fetchall()
    return seleccion



if __name__ == '__main__':    
    app.run(debug=True, host='127.0.0.1', port =443)
    #, ssl_context=('micertificado.pem', 'llaveprivada.pem'))


