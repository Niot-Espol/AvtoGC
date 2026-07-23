AVTOGC

AVTOGC es una aplicación web que consulta cursos y actividades académicas desde Canvas y permite sincronizarlas con Google Calendar.

El proyecto utiliza:

    -Backend: Python 3.12 y FastAPI.

    -Frontend: React, JavaScript/JSX y Vite.

    -Base de datos: SQLite.

    -Integraciones: Canvas API y Google Calendar API.

    -Control de versiones: Git y GitHub.

Cada integrante puede clonar la rama main, crear su propia rama, ejecutar el proyecto en su computadora y subir únicamente los archivos que haya modificado o agregado.

1. Estructura esperada
```
AvtoGC/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── services/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── main.py
│   │   └── models.py
│   ├── credentials/
│   └── .venv/                 # Solo local, no se sube
├── frontend/
│   ├── api/
│   ├── components/
│   ├── src/
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
├── requirements.txt
├── .gitignore
└── README.md
```
2. Requisitos

Cada integrante debe instalar en su computadora:

    -Git.
    -Python 3.12 de 64 bits.
    -Node.js LTS.
    -npm.
    -Visual Studio Code.
    -Comprobar las versiones:

COMANDOS PARA VERIFICAR 
-git --version
-py -3.12 --version
-node --version
-npm --version

El backend debe ejecutarse con Python 3.12.

3. Clonar el proyecto desde main

cd "C:\Users\TU_USUARIO\Desktop"
git clone https://github.com/Niot-Espol/AvtoGC.git
cd AvtoGC
git switch main
git pull origin main
git status

-Resultado esperado:

On branch main
Your branch is up to date with 'origin/main'.
nothing to commit, working tree clean

4. Crear una rama personal

No se debe trabajar directamente sobre main.

git switch main
git pull origin main
git switch -c design/nombre-del-cambio

Ejemplos:

git switch -c design/mejorar-login
git switch -c design/dashboard-responsive
git switch -c feat/listado-tareas
git switch -c fix/error-fechas

-Comprobar la rama activa:

git branch --show-current

*Backend*

5. La primera vez que crean el entorno virtual

Desde la raíz del repositorio:

cd backend
py -3.12 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python --version

Debe mostrar Python 3.12.x.

6. Instalar dependencias (solo una vez)

python -m pip install --upgrade pip
python -m pip install -r ..\requirements.txt
python -m pip check

Resultado esperado:

No broken requirements found.

Las dependencias quedan en backend/.venv/. Esa carpeta es local y no se sube a GitHub.

7. Iniciar el backend (ya si quieren abrirlo más seguido solo deben poner estos comandos)

.\backend\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8000 --app-dir .\backend

EJEMPLO:
PS C:\Users\sagea\Desktop\Proyecto de Google calendar\AvtoGC> .\backend\.venv\Scripts\Activate.ps1
(.venv) PS C:\Users\sagea\Desktop\Proyecto de Google calendar\AvtoGC> python -m uvicorn app.main:app --reload --port 8000 --app-dir .\backend
funciona cuando sale la siguiente respuesta 
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     127.0.0.1:32811 - "OPTIONS /api/canvas/status HTTP/1.1" 200 OK

*Frontend*

8. Instalar dependencias

Abrir una segunda terminal:

cd frontend
npm install
Las dependencias quedan en frontend/node_modules/. Esa carpeta es local y no se sube a GitHub.

9. Iniciar el frontend (ya si quieren abrirlo más seguido solo deben poner estos comandos)

npm run dev

Resultado esperado:

VITE ready
Local: http://localhost:5173/

Abrir:

http://localhost:5173

La terminal debe permanecer abierta.

Dependencias y archivos locales

10. Qué no se sube

No se suben:
```
backend/.venv/
frontend/node_modules/
frontend/dist/
__pycache__/
.env
.env.local
client_secret.json
token.json
*.db
*.sqlite
*.sqlite3
```

Estas carpetas y archivos se generan o configuran localmente.

11. Qué sí se sube

Sí se suben:

requirements.txt
frontend/package.json
frontend/package-lock.json
código fuente modificado o agregado

Sobre package-lock.json

-package-lock.json no contiene todas las dependencias instaladas. Solo registra las versiones exactas que npm debe instalar.

Debe permanecer en GitHub para que todos obtengan versiones compatibles.

Solo se modifica cuando:
    -Se agrega o elimina una dependencia.
    -Se actualiza una dependencia.
    -Se regenera porque contenía una URL incorrecta.
    -No debe agregarse a .gitignore.