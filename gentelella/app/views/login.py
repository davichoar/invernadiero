from django.shortcuts import render, redirect
from django.template import loader
from django.http import HttpResponse

from app.models import Usuario



def index(request,
          template='app/loginShido.html',
          extra_context=None):
    print(type(Usuario.objects.raw('Select * from app.usuario')))
    print(type(Usuario.objects.all()))
    if request.method == 'POST':
        print('LLEGO POST')
        nombreUsuario = request.POST['nombreUsuario']
        contraseña = request.POST['contraseña']
        #usuario = Usuario.objects.raw('Select * from app.usuario where nombreusuario='+nombreUsuario+' and  contrasena = '+contraseña)
        #listaUsuario = Usuario.objects.raw('Select * from public.app.usuario')
        #listaUsuario = Usuario.objects.all()
        usuario = None
        try:
            usuario = Usuario.objects.get(nombreusuario=nombreUsuario, contrasena=contraseña)
        except:
            print('Error al consultar base de datos')

        if usuario is not None:
            print(usuario.nombres)
            print(usuario.apellidopaterno)
            return redirect('index')


    ##context = {
    #    'userList': user,
    #}
    context = {

     }
    if extra_context is not None:
        context.update(extra_context)
    return render(request, template, context)