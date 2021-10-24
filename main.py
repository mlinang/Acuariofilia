import os
from flask.helpers import flash
from werkzeug.utils import secure_filename
from flask import flash
from markupsafe import escape
from forms.forms import *
from flask import Flask, render_template, url_for, redirect, jsonify, request, session
from db import *
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

UPLOAD_FOLDER = os.path.abspath("static/images/Post")
ALLOWED_EXTENSIONS = set(["png","jpg", "jpeg"])

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
@app.route('/feed')
def feed():
    sql ="SELECT * FROM Post"
    db = get_db()
    cursorObj = db.cursor()
    cursorObj.execute(sql)
    posts = cursorObj.fetchall()
    return render_template("feed.html", posts=posts)

    
"""     if 'fullname' in session and (session['rol'] == 1 or session['rol'] ==2) :
        sql ="SELECT * FROM Post"
        db = get_db()
        cursorObj = db.cursor()
        cursorObj.execute(sql)
        posts = cursorObj.fetchall()
        return render_template("feed.html", posts=posts)
        
    else:
        return redirect('login') """


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

@app.route('/editProduct', methods=['GET', 'POST'])
def editProduct():
    id = request.args.get('id')
    if request.method == 'GET':
        form = Postform()
        db = get_db()
        sql = f'SELECT * FROM Post WHERE id = {id}'
        cursorObj = db.cursor()
        cursorObj.execute(sql)
        products = cursorObj.fetchall()[0]
        return render_template('editProduct.html', form=form, products=products)
    
    if request.method == 'POST':
        id = request.form['id']
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        precio = request.form['precio']
        cantidad = request.form['cantidad']
        estado = request.form['estado']
        imagen = request.files['imagen']
        if imagen.filename != "":
            filename = secure_filename(imagen.filename)
            imagen.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))     
        else:
            filename = request.form['filename']        
        db = get_db()
        sql = 'UPDATE products SET nombre = ?, descripcion = ?, precio = ?, cantidad = ?, url = ?, estado = ? WHERE id = ?'        
        result = db.execute(sql, (nombre, descripcion, precio, cantidad, filename, estado, id)).rowcount
        db.commit()
        if result > 0:
            flash('Se actualizó el registro exitosamente')
        else:
            flash('No se pudo actualizar el registro')            
        return redirect(url_for('product'))
        

@app.route('/deleteProduct', methods=['GET', 'POST'])
def deleteProduct():
    id = request.args.get('id')
    sql = "DELETE FROM products WHERE id = ?"
    db = get_db()
    db.execute(sql, (id))
    db.commit()
    db.close()
    flash('Registro eliminado exitosamente')
    return redirect(url_for('product'))

@app.route('/postdetail')
def postdetail():
    id = request.args.get('codigo')
    sql = "SELECT * FROM Post WHERE id = ?"
    db = get_db()
    cursorObj = db.cursor()
    cursorObj.execute(sql, (id))
    posts = cursorObj.fetchall()
    return render_template("postdetail.html", posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ""
    form = LoginForm()
    if(form.validate_on_submit()):                
       # email = form.email.data
        email = escape(form.email.data.strip())
        password = escape(form.password.data.strip())
        sql = f'SELECT * FROM User WHERE email = "{email}"'
        db = get_db()
        cursorObj = db.cursor()
        cursorObj.execute(sql)       
        usuarios = cursorObj.fetchall()
        if len(usuarios) > 0:
            contrasenaHas = usuarios[0][4]
            if check_password_hash(contrasenaHas, password):            
                session.clear()
                session['id'] = usuarios[0][0]
                session['fullname'] = usuarios[0][1] + " " + usuarios[0][2]
                session['correo'] = usuarios[0][3]
                session['rol'] = usuarios[0][7]
                session['password'] = contrasenaHas
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
        session.pop('id')
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

@app.route('/restablecercontrasena')
def passforget():
    session.clear()
    return render_template("restablecercontrasena.html")

@app.route('/recordarpassword')
def recordarpassword():
    return render_template("recordarpassword.html") 

@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html")      

@app.route('/search', methods=['GET', 'POST'])
def search():
    form = searchForm()
    if request.method == 'POST':
        clave = request.form['palabra']
        sql = f'SELECT UserId,name, lastname, email,birthay,gender,CreationDate,ProfilePicURL FROM User WHERE name LIKE "%{clave}%" OR lastname LIKE "%{clave}%"'
        db = get_db()
        cursorObj = db.cursor()
        cursorObj.execute(sql)       
        Sresult = cursorObj.fetchall()
        if len(Sresult) > 0:
            return render_template("search.html", Sresult=Sresult)                               
        else:
            flash(f'La busqueda no arrojo resultados')
            return redirect(url_for('feed'))
    if request.method == 'GET':
        return render_template("search.html")

@app.route('/perfil')
def perfil():
    return render_template("perfil.html") 

if __name__ == '__main__':    
    app.run(debug=True, host='127.0.0.1', port =443)
    #, ssl_context=('micertificado.pem', 'llaveprivada.pem'))

   




