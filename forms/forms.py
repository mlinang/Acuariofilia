from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, IntegerField, SelectField, FileField, RadioField,TextAreaField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(message="Este campo es requerido")])
    password = PasswordField('Password', validators=[DataRequired(message="Este campo es requerido")])
    recordar = BooleanField('Recordar usuario')

class Postform(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()], render_kw={"placeholder": "¿Quieres publicar una imagen?"})
    descripcion = TextAreaField('Descripción',  validators=[DataRequired()])
    imagen = StringField('Imagen')
    #estado = SelectField('Estado', choices = [('Activo', 'Activo'), ('Activo', 'Activo'), ('Inactivo', 'Inactivo')])

class UserForm(FlaskForm):
    firstname = StringField('firstname', validators=[DataRequired(message="Este campo es requerido")], render_kw={"placeholder": "Su nombre"})
    lastname = StringField('Lastname', validators=[DataRequired(message="Este campo es requerido")], render_kw={"placeholder": "su apellido"})
    password = PasswordField('password', validators=[DataRequired(message="Este campo es requerido")], render_kw={"placeholder": "Digite contraseña"})
    passconf = PasswordField('passconf', validators=[DataRequired(message="Este campo es requerido")], render_kw={"placeholder": "Confirmar contraseña"})
    email = StringField(u'Mailing Address', validators=[DataRequired(message="Este campo es requerido")], render_kw={"placeholder": "Digite correo"})
    gender= SelectField('Genero', choices = [('Masculino'), ('Femenino'), ('Otro')], default="Please choose",)
    Birthdate = DateField('Birthdate', validators=[DataRequired(message="Este campo es requerido")],format='%d-%m-%y')

class searchForm(FlaskForm):
    palabra = StringField('palabra', validators=[DataRequired(message="Este campo es requerido")], render_kw={"placeholder": "Buscar Usuario"})
  

    
    

    
