import os
from flask.helpers import flash
from werkzeug.utils import secure_filename
from markupsafe import escape
from forms.forms import Postform, LoginForm, UserForm
from flask import Flask, render_template, url_for, redirect, request, session
from db import get_db
from utils import isEmailValid, isPasswordValid
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

UPLOAD_FOLDER = os.path.abspath("/home/mlinan/Acuariofilia/static/images/Post")
UPLOAD_FOLDER2 = os.path.abspath("/home/mlinan/Acuariofilia/static/images/Perfil")
ALLOWED_EXTENSIONS = set(["png","jpg", "jpeg"])

app = Flask(__name__)
app.secret_key = os.urandom(24)
#app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/feed')
#@login_required
def feed():
    #@pablo@ esta condicion es por si alguien escribe directamente /feed en el navegador y no se encuentra logeado lo manda al login
    #probando esto me di cuenta que le doy logout me manda al login, pero si escribo /feed puedo abrirlo porque no ha salido de la sesion.
    if 'fullname' not in session:
        return redirect('login')
    else:
        usu= session['id']
        sql ="SELECT * FROM Post order by creationDate desc limit 10"
        posts = selectSQLite(sql)
        sql =f'SELECT * FROM Post WHERE UserId = {usu} order by creationDate desc limit 20'
        postown = selectSQLite(sql)
        """ return render_template("feed.html", posts=posts, postown=postown) """
        #@pablo@ active la condicion para que si no tiene una sesion abierta lo envie al login.
        sql ="SELECT * FROM Post"
        posts = selectSQLite(sql)
        return render_template("feed.html", posts=posts, postown=postown)


@app.route('/addPost', methods=['GET', 'POST'])
def addPost():
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    if 'fullname' not in session:
        return redirect('login')
    else:
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

@app.route('/addProfilePic', methods=['GET', 'POST'])
def addProfilePic():
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER2
    up_query = ""
    if 'fullname' not in session:
        return redirect('login')
    else:
        form = Postform()
        if request.method == 'POST':
            imagen = request.files['imagen']
            filename = secure_filename(imagen.filename)
            imagen.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            db = get_db()
            up_query = f"UPDATE User SET ProfilePicURL = '{filename}' WHERE UserId = '{session['id']}' ";
            result = db.execute(up_query).rowcount
            db.commit()
            if result>0:
                mensaje ="Imagen de perfil guardada exitosamente"
            else:
                mensaje= "Error al guardar imagen"
            flash(mensaje)
            return redirect(url_for('feed', mensajeExitoso=mensaje))
        return render_template('Perfil.html', form=form)

@app.route('/deleteComm', methods=['GET', 'POST'])
def deleteComm():
    if 'fullname' not in session:
        return redirect('login')
    else:
        msg='Comentario eliminado exitosamente'
        id = request.args.get('codigo')
        postId=request.args.get('postId')
        sql = f'DELETE FROM Comments WHERE CommentId = {id}'
        updateSQLite(sql,"cerrar")
        flash(msg)
        return redirect(url_for('postdetail', codigo=postId))

@app.route('/deletePost', methods=['GET', 'POST'])
def deletePost():
    if 'fullname' not in session:
        return redirect('login')
    else:
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
    if 'fullname' not in session:
        return redirect('login')
    else:
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
    if 'fullname' not in session:
        return redirect('login')
    else:
        idp = request.args.get('codigo')
        sql = f'SELECT * FROM Post , User WHERE User.UserId=Post.UserId AND Post.PostId = {idp}'
        postsel= selectSQLite(sql)
        sql = f'SELECT * from Comments, User WHERE User.UserId=Comments.UserId AND Comments.PostId = {idp}'
        comPost= selectSQLite(sql)
        return render_template("postdetail.html", postsel=postsel,comPost=comPost)

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
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
                flash('Usuario y/o Clave incorrecta')
                return redirect(url_for('login'))
        else:
                flash('Usuario y/o Clave incorrecta')
    return render_template("Login.html", form=form)


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
        gender = request.form['gender']
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
            error = "El correo ingresado es inv??lido"
            flash(error)
        if not isPasswordValid(password):
            error = "La contrase??a debe tener entre 8 y 16 caracteres, al menos un d??gito, al menos una min??scula y al menos una may??scula, sin caracteres especiales."
            flash(error)
        if error is not None:
            # Ocurri?? un error
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
    if 'fullname' not in session:
        return redirect('login')
    else:
        error1 = None
        form = UserForm()
        if request.method == 'POST':
            currentPass = request.form['password']
            newPass1 = request.form['newPass1']
            newPass2 = request.form['newPass2']

            if not check_password_hash(session['password'], currentPass):    #si la clave hash de la sesion activa no coincide con la ingresada
                error1 = "Error al validar la contrase??a actual"   #ojo, si no hay sesi??n activa da error
                flash(error1)
            if newPass1 != newPass2:    #si los dos campos de nueva contrase??a no coinciden
                error1 = "Error al validar la nueva contrase??a"
                flash(error1)
            if not isPasswordValid(newPass1):
                error1= "La contrase??a debe tener entre 8 y 16 caracteres, al menos un d??gito, al menos una min??scula y al menos una may??scula, sin caracteres especiales."
                flash(error1)
            else:
                newPassHash = generate_password_hash(newPass1)  #genera nueva contrase??a encriptada
            if error1 is not None:
                print(error1)
                return render_template("cambiarcontrasena.html", form=form)

            else:
                db = get_db()
                sql1 = f'UPDATE User SET password = ? WHERE email = ?'
                result = db.execute(sql1, (newPassHash, session['correo'])).rowcount
                db.commit()
                if result > 0:
                    flash('Se actualiz?? la contrase??a exitosamente')
                else:
                    flash('No se pudo actualizar la contrase??a')
        return render_template("cambiarcontrasena.html", form=form)


@app.route('/makeAdmin', methods=['GET', 'POST']) #ojo... debe haber siempre una sesion activa
def makeAdmin():
    if session['rol']!=1:
        return redirect('login')
    else:
        userId = request.args.get('userId')
        sql = f'UPDATE User SET role = 1 WHERE UserId = {userId}' #rol 1: admin, al usuario del post seleccionado
        updateSQLite(sql, "cerrar")
        flash('Se han otorgado privilegios de administrador al usuario de forma exitosa')
        return redirect(url_for('perfil', codigo=userId))

@app.route('/restablecercontrasena')
def restablecercontrasena():
    return render_template("restablecercontrasena.html")

@app.route('/editProfile', methods=['POST']) #ojo... debe haber siempre una sesion activa
def editProfile():
    error = "Sus Datos han sido Actualizados Correctamente."
    flash(error)
    if 'id' in session:
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        birthday = request.form['nacimiento']
        #gender=request.form['genero']
        phone = request.form['telefono']
        profession = request.form['profesion']
        country = request.form['pais']
        userId = session['id']
        error2 = birthday
        flash(error2)

        sql = f"UPDATE User SET name = '{nombre}', lastName = '{apellido}', birthay = '{birthday}', country='{country}', phone={phone}, profesion='{profession}' WHERE UserId = { session['id'] };"

        updateSQLite(sql, "cerrar")
        return redirect(url_for('perfil', codigo=session['id']))
    return redirect(url_for('feed'))

@app.route('/dashboard')
def dashboard():
    if session['rol']!=1:
        return redirect('feed')
    else:
        return render_template("dashboard.html")

@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'fullname' not in session:
        return redirect('login')
    else:
        if request.method == 'POST':
            clave = request.form['palabra']
            sql = f'SELECT UserId,name, lastname, email,birthay,gender,CreationDate,ProfilePicURL,about FROM User WHERE name LIKE "%{clave}%" OR lastname LIKE "%{clave}%"'
            Sresult = selectSQLite(sql)
            sql = f'SELECT * FROM Post WHERE title LIKE "%{clave}%"'
            posts = selectSQLite(sql)
            if len(Sresult) or len(posts) > 0:
                return render_template("search.html", Sresult=Sresult, posts=posts)
            else:
                flash('La busqueda no arrojo resultados')
                return redirect(url_for('search'))
        if request.method == 'GET':
            return render_template("search.html")

@app.route('/perfil')
def perfil():
    if 'fullname' not in session:
        return redirect('login')
    else:
        if request.method == 'GET':
            idsel = request.args.get('codigo')
            sql = f'SELECT * FROM User WHERE UserId = {idsel}'
            psel = selectSQLite(sql)
            sql = f'SELECT * FROM User, Messages WHERE UserDe = {idsel} AND user.UserId=Messages.UserPara order by CreationDate desc limit 20'
            msgs = selectSQLite(sql)
            if len(msgs)==0:
                msgs="vacio"
            return render_template("perfil.html", psel=psel[0], msgs=msgs)

@app.route('/addcomm', methods=['GET','POST'])
def addcomm():
    if 'fullname' not in session:
        return redirect('login')
    else:
        postsel = request.args.get('codigo') #recupera el valor de la variable codigo enviada por GET
        contenido = request.form['comentario']
        id=session['id']
        time= datetime.now()
        if request.method == 'POST':
            sql=(f"INSERT INTO Comments (Content, PostId, UserId, CreationDate) VALUES('{contenido}',{postsel},{id},'{time}')")
            updateSQLite(sql, "cerrar")
        return redirect(url_for('postdetail', codigo=postsel))

@app.route('/sendmes', methods=['GET', 'POST'])
def sendmes():
    if request.method == 'POST':
        psel = request.args.get('codigo')
        contenido = request.form['msg']
        de=session['id']
        time= datetime.now()
        sql=(f"INSERT INTO Messages (Content, UserPara, UserDe, CreationDate) VALUES('{contenido}',{psel},{de},'{time}')")
        db = get_db()
        db.execute(sql)
        db.commit()

    return redirect(url_for('perfil', codigo=psel))


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


