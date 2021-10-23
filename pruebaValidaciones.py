from hashlib import sha512
from werkzeug.security import generate_password_hash, check_password_hash


ms = sha512(b'python')
print(f'ms: {ms.digest()}')

ms = sha512(b'Python')
print(f'ms: {ms.digest()}')

contraseña = generate_password_hash('pepe123')
print('c:', contraseña)

if check_password_hash(contraseña, 'Pepe123'):
    print('Bienvenido')
else:
    print('Contraseña inccorrecta')



