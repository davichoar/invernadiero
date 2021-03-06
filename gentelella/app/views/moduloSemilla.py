from django.db import transaction
from django.db.models import Max
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, render_to_response
from datetime import datetime
from django.template import loader
from django.urls import reverse
from app.permissions import *

from app.models import Zona, Tipozona, Historiainvernadero, Historiazona, Modulosemilla, Historiamodulo, Semilla, \
    Historiasemilla, Tipoplanta, Planta, Foto, Cronograma

ID_TIPO_ZONAS_SEMILLAS = 1
CANTIDAD_CADENA_MAXIMA = 250
CODIGO_GENERAL_COMBO = -1
def crear(request,
          template='app/modulosemilla/crear.html',
          extra_context=None):
    try:
        idInvernadero = int(request.session.get('idInvernadero'))
        listaZonas = Zona.objects.filter(idinvernadero=idInvernadero, idtipozona=ID_TIPO_ZONAS_SEMILLAS,habilitado=True)
    except Exception as e:
        print(e)
        request.session['mensajeCrearEditarError'] = True
        return redirect('moduloSemillaListar')


    context = {'listaZonas': listaZonas,
                   'nombreUsuario': request.session.get('nomreUsuario'),
                   'nombreInvernadero': request.session.get('nombreInvernadero'),
                   }
    if request.method == 'GET':
        if not 'idUsuarioActual' in request.session:
            return redirect('loginIndex')
        if not 'idInvernadero' in request.session:
            return redirect('escogerInvernadero')
        if not tienepermiso(request, "Crear Modulosemilla"):
            return accesodenegado(request)
        print('CREAR MODULO DE SEMILLAS')
        return render(request, template, context)
    elif request.method == 'POST':
        if not 'idUsuarioActual' in request.session:
            return redirect('loginIndex')
        if not 'idInvernadero' in request.session:
            return redirect('escogerInvernadero')
        if not tienepermiso(request, "Crear Modulosemilla"):
            return accesodenegado(request)

        if "b_aceptar" in request.POST:

            mensajeError = None
            try:
               mensajeError = grabarData(request,None)
            except Exception as e:
                mensajeError = "No se puede crear el modulo en este momento"
                print("No se puede crear el modulo en este momento")
                print(e)

            if mensajeError is not None:
                print("MENSAJE ERROR CREAR MODULO DE SEMILLAS")
                try:
                    modulo = obtenerModuloRequest(request)
                except Exception as e:
                    modulo = None
                    print("Error obteniendo la data del request")
                context = {"modulo":modulo,
                           'listaZonas': listaZonas,
                           'nombreUsuario': request.session.get('nomreUsuario'),
                           'nombreInvernadero': request.session.get('nombreInvernadero'),
                           'mensajeError': mensajeError,
                           }
                return render(request, template, context)
            else:
                request.session['mensajeModuloCrear'] = True
        return redirect('moduloSemillaListar')
    else:
        return redirect('moduloSemillaListar')


def listar(request,
          extra_context=None):
    #template = loader.get_template('app/zonainvernadero/lista.html')
    template = "app/modulosemilla/lista.html"
    listaModulos = []
    if request.method == 'GET':
        if not 'idUsuarioActual' in request.session:
            return redirect('loginIndex')
        if not 'idInvernadero' in request.session:
            return redirect('escogerInvernadero')
        if not tienepermiso(request, "Ver Modulosemilla"):
            return accesodenegado(request)

        print('LISTAR MODULOS SEMILLAS')
        listaIdZonas = []
        try:
            idInvernadero = int(request.session.get('idInvernadero'))
            listaZonas = Zona.objects.filter(idinvernadero=idInvernadero,idtipozona = ID_TIPO_ZONAS_SEMILLAS, habilitado=True)
            for zona in listaZonas:
                listaIdZonas.append(zona.idzona)
        except Exception as e:
            print(e)
            listaZonas = None

        mensajeCreacion = False
        mensajeEliminar = False
        mensajeCrearEditarError = False
        mensajeObtenerZonaError = False

        if listaZonas != None:
            if "b_buscar" in request.GET:
                valorBusqueda = request.GET.get('textoBusqueda')
                print(valorBusqueda)
                if (valorBusqueda is None):
                    valorBusqueda = ""
                try:
                    listaModulos = Modulosemilla.objects.filter(idzona__in = listaIdZonas,nombre__icontains=valorBusqueda, habilitado=True)
                except Exception as e:
                    print(e)
                    listaModulos = None
            else:
                try:
                    listaModulos = Modulosemilla.objects.filter(idzona__in = listaIdZonas,habilitado=True)
                except Exception as e:
                    print(e)
                    listaModulos = None

            mensajeCreacion = request.session.pop('mensajeModuloCrear', False)
            mensajeEliminar = request.session.pop('mensajeModuloEliminar', False)
            mensajeCrearEditarError = request.session.pop('mensajeCrearEditarError', False)

            if listaModulos:
                listaModulos = listaModulos.order_by('idmodulo')

        else:
            mensajeObtenerZonaError = True

        print('Lista de modulos')
        print(listaModulos)
        context = {"listaModulos": listaModulos, 'nombreUsuario': request.session.get('nomreUsuario'),
                   'nombreInvernadero': request.session.get('nombreInvernadero'),"mensajeCreacion": mensajeCreacion,"mensajeEliminacion": mensajeEliminar,"mensajeCrearEditarError":mensajeCrearEditarError,"mensajeObtenerZonaError":mensajeObtenerZonaError}
        return render(request, template, context)

    elif request.method == 'POST':
        if "b_crear" in request.POST:
            return redirect('moduloSemillaCrear')
    ###Me parece q podriamos borrar toda esta webada de abajo
    if not 'idUsuarioActual' in request.session:
        return redirect('loginIndex')
    if not 'idInvernadero' in request.session:
        return redirect('escogerInvernadero')
    if not tienepermiso(request, "Ver Modulosemilla"):
        return accesodenegado(request)
    context = {}
    return render(request, template, context)

def validarRangoCondiciones(actual,min,max):

    actual = float(actual)
    min = float(min)
    max = float(max)
    if (actual >= min) and (actual <= max):
        return True
    else:
        return False

        
def contextParaGrilla(request, context, modulo):
    context['rangeFilas'] = range(1, modulo.filas + 1)
    context['rangeColumnas'] = range(1, modulo.columnas + 1)
    context['mostrarModalCrear'] = request.session.pop('mensajeSemillaCrear', False)
    context['mostrarModalEliminar'] = request.session.pop('mensajeSemillaEliminar', False)
    semillas = Semilla.objects.filter(idmodulo=modulo.idmodulo, habilitado=True)
    listaSemillas = dict()
    for semilla in semillas:
        try:
            historiaSemilla = Historiasemilla.objects.filter(idsemilla=semilla.idsemilla).order_by('-fecharegistro')[0]
        except:
            continue
        posx = historiaSemilla.posx
        if not posx in listaSemillas:
            listaSemillas[posx] = dict()
        listaSemillas[posx][historiaSemilla.posy] = (semilla, Tipoplanta.objects.get(idtipoplanta = semilla.idtipoplanta).nombrecomun)
    context['listaSemillas'] = listaSemillas
    print(listaSemillas)

def detalle(request,idModulo):

    template = 'app/modulosemilla/verEditar.html'
    modulo = Modulosemilla.objects.get(idmodulo=idModulo)
    semillasModulo = Semilla.objects.filter(idmodulo=idModulo, habilitado=True)

    if len(semillasModulo) > 0:
        moduloConSemillas = True
    else:
        moduloConSemillas = False
    try:
        idInvernadero = int(request.session.get('idInvernadero'))
        listaZonas = Zona.objects.filter(idinvernadero=idInvernadero, idtipozona=ID_TIPO_ZONAS_SEMILLAS,habilitado=True)
    except Exception as e:
        print(e)
        request.session['mensajeCrearEditarError'] = True
        return redirect('moduloSemillaListar')


    try:
        historiaModulo = Historiamodulo.objects.filter(idmodulo=idModulo).order_by('-fecharegistro')[0]
    except Exception as e:
        historiaModulo = None
        print(e)

    if historiaModulo:
        temperaturaok = validarRangoCondiciones(historiaModulo.temperatura,modulo.temperaturamin,modulo.temperaturamax)
        humedadTierraok = validarRangoCondiciones(historiaModulo.humedadtierra,modulo.humedadtierramin,modulo.humedadtierramax)
        humedadAmbienteok = validarRangoCondiciones(historiaModulo.humedadambiente,modulo.humedadambientemin,modulo.humedadambientemax)
        nivelAguaok = validarRangoCondiciones(historiaModulo.nivelagua,modulo.nivelaguamin,modulo.nivelaguamax)
        co2ok = validarRangoCondiciones(historiaModulo.concentracionco2,modulo.concentracionco2min,modulo.concentracionco2max)
    else:
        temperaturaok = None
        humedadTierraok = None
        humedadAmbienteok = None
        nivelAguaok = None
        co2ok = None

    hayFotos = (len(Foto.objects.filter(idmodulo = idModulo)) > 0)

    hayCronograma = (len(Cronograma.objects.filter(idmodulo=idModulo)) > 0)
    
    context = {"moduloConSemillas":moduloConSemillas,"historiaModulo": historiaModulo, "listaZonas": listaZonas, "modulo": modulo,
               'nombreUsuario': request.session.get('nomreUsuario'),
               'nombreInvernadero': request.session.get('nombreInvernadero'), "editable": False,
               "temperaturaok": temperaturaok, "humedadTierraok": humedadTierraok,
               "humedadAmbienteok": humedadAmbienteok, "nivelAguaok": nivelAguaok, "co2ok": co2ok, 'hayFotos': hayFotos,'hayCronograma':hayCronograma}

    if request.method == 'GET':
        if not 'idUsuarioActual' in request.session:
            return redirect('loginIndex')
        if not 'idInvernadero' in request.session:
            return redirect('escogerInvernadero')
        if not tienepermiso(request, "Ver Modulosemilla"):
            return accesodenegado(request)
        print('Mostrar Modulo de Semilla')
        ## context es el mismo de arriba
        context['editable'] = False ## es un saludo a la bandera, solo para aclarar que la vista no sera editable
        contextParaGrilla(request, context, modulo)
        return render(request, template, context)

    elif request.method == 'POST':
        if "b_cronograma" in request.POST:
            return redirect('moduloSemillaCronograma', idModulo = idModulo)

        if "b_editar" in request.POST:
            if not 'idUsuarioActual' in request.session:
                return redirect('loginIndex')
            if not 'idInvernadero' in request.session:
                return redirect('escogerInvernadero')
            if not tienepermiso(request, "Editar Modulosemilla"):
                return accesodenegado(request)
            print('Editar Modulo Semilla')
            context['editable'] = True
            return render(request, template, context)
        if "b_aceptar" in request.POST:
            if not 'idUsuarioActual' in request.session:
                return redirect('loginIndex')
            if not 'idInvernadero' in request.session:
                return redirect('escogerInvernadero')
            if not tienepermiso(request, "Editar Modulosemilla"):
                return accesodenegado(request)
            print('Aceptar Modulo Semilla')
            mensajeError = None
            try:
               mensajeError = grabarData(request,idModulo)
            except Exception as e:
                mensajeError = "No se puede crear la zona en este momento"
                print(e)
            try:
                modulo = obtenerModuloRequest(request)
            except Exception as e:
                print(e)
                print("Error obteniendo la data del request")
                if mensajeError is not None:
                    mensajeError = "Ocurrió un error inesperado. Intente editar más tarde"

            context['modulo'] = modulo
            if mensajeError:

                context['editable'] = True
                context['mensajeError'] = mensajeError

                return render(request, template, context)
            else:
                if historiaModulo:
                    temperaturaok = validarRangoCondiciones(historiaModulo.temperatura, modulo.temperaturamin,modulo.temperaturamax)
                    humedadTierraok = validarRangoCondiciones(historiaModulo.humedadtierra, modulo.humedadtierramin,modulo.humedadtierramax)
                    humedadAmbienteok = validarRangoCondiciones(historiaModulo.humedadambiente,modulo.humedadambientemin, modulo.humedadambientemax)
                    nivelAguaok = validarRangoCondiciones(historiaModulo.nivelagua, modulo.nivelaguamin,modulo.nivelaguamax)
                    co2ok = validarRangoCondiciones(historiaModulo.concentracionco2, modulo.concentracionco2min,modulo.concentracionco2max)

                context['editable'] = False
                context['mostrarModalEditar'] = True
                context['temperaturaok'] = temperaturaok
                context['humedadTierraok'] = humedadTierraok
                context['humedadAmbienteok'] = humedadAmbienteok
                context['nivelAguaok'] = nivelAguaok
                context['co2ok'] = co2ok
                contextParaGrilla(request, context, modulo)

                return render(request, template, context)

        if "b_cancelar" in request.POST :
            if not 'idUsuarioActual' in request.session:
                return redirect('loginIndex')
            if not 'idInvernadero' in request.session:
                return redirect('escogerInvernadero')
            if not tienepermiso(request, "Ver Modulosemilla"):
                return accesodenegado(request)
            ## context es el mismo de arriba
            context['editable'] = False  ## es un saludo a la bandera, solo para aclarar que la vista no sera editable
            contextParaGrilla(request, context, modulo)
            return render(request, template, context)
        if "b_aceptar_modal" in request.POST:
            if not 'idUsuarioActual' in request.session:
                return redirect('loginIndex')
            if not 'idInvernadero' in request.session:
                return redirect('escogerInvernadero')
            if not tienepermiso(request, "Eliminar Modulosemilla"):
                return accesodenegado(request)
            print("Aceptar Modal")

            if moduloConSemillas:
                context['editable'] = False
                context['mensajeError'] = "No se puede eliminar el módulo porque hay semillas asociadas"

            try:
                eliminarModulo(request, idModulo)
                request.session['mensajeModuloEliminar'] = True
            except Exception as e:
                print(e)

            return redirect('moduloSemillaListar')
        else:
            return redirect('moduloSemillaListar')


def eliminarModulo(request,idModulo):
    idUsuarioActual = int(request.session.get('idUsuarioActual'))
    modulo,created = Modulosemilla.objects.update_or_create(
        idmodulo=idModulo, defaults={"habilitado":False,"idusuarioauditado":idUsuarioActual})
    print(created)
    return


def obtenerModuloRequest(request, idModulo = None):
    moduloDataLlenada = Modulosemilla()

    nombreObtenido = request.POST.get('nombre')
    codigoModulo = request.POST.get('codigoModulo')
    idzona = request.POST.get('zona')
    tempIdeal = request.POST.get('tempIdeal')
    tempMin = request.POST.get('tempMin')
    tempMax = request.POST.get('tempMax')
    humTierraIdeal = request.POST.get('humedadTierraIdeal')
    humTierraMin = request.POST.get('humedadTierraMin')
    humTierraMax = request.POST.get('humedadTierraMax')
    humAmbIdeal = request.POST.get('humedadAmbienteIdeal')
    humAmbMin = request.POST.get('humedadAmbienteMin')
    humAmbMax = request.POST.get('humedadAmbienteMax')
    co2Ideal = request.POST.get('co2Ideal')
    co2Min = request.POST.get('co2Min')
    co2Max = request.POST.get('co2Max')
    nivelAguaIdeal = request.POST.get('nivelAguaIdeal')
    nivelAguaMin = request.POST.get('nivelAguaMin')
    nivelAguaMax = request.POST.get('nivelAguaMax')
    filas = request.POST.get('filas')
    columnas = request.POST.get('columnas')

    moduloDataLlenada.idmodulo = idModulo
    moduloDataLlenada.nombre = nombreObtenido
    moduloDataLlenada.codigomodulojson = codigoModulo

    if idzona != None:
        moduloDataLlenada.idzona = int(idzona)

    moduloDataLlenada.temperaturaideal = tempIdeal
    moduloDataLlenada.temperaturamin = tempMin
    moduloDataLlenada.temperaturamax = tempMax
    moduloDataLlenada.humedadtierraideal = humTierraIdeal
    moduloDataLlenada.humedadtierramin = humTierraMin
    moduloDataLlenada.humedadtierramax = humTierraMax
    moduloDataLlenada.humedadambienteideal = humAmbIdeal
    moduloDataLlenada.humedadambientemin = humAmbMin
    moduloDataLlenada.humedadambientemax = humAmbMax
    moduloDataLlenada.concentracionco2ideal = co2Ideal
    moduloDataLlenada.concentracionco2min = co2Min
    moduloDataLlenada.concentracionco2max = co2Max
    moduloDataLlenada.nivelaguaideal = nivelAguaIdeal
    moduloDataLlenada.nivelaguamin = nivelAguaMin
    moduloDataLlenada.nivelaguamax = nivelAguaMax
    moduloDataLlenada.filas = int(filas)
    moduloDataLlenada.columnas = int(columnas)

    return moduloDataLlenada

def grabarData(request,idModulo):
    print('GRABAR DATA')

    nombreObtenido = request.POST.get('nombre')
    codigoModuloObtenido = request.POST.get('codigoModulo')
    idzona = request.POST.get('zona')
    tempIdeal = request.POST.get('tempIdeal')
    tempMin = request.POST.get('tempMin')
    tempMax = request.POST.get('tempMax')
    humTierraIdeal = request.POST.get('humedadTierraIdeal')
    humTierraMin = request.POST.get('humedadTierraMin')
    humTierraMax = request.POST.get('humedadTierraMax')
    humAmbIdeal = request.POST.get('humedadAmbienteIdeal')
    humAmbMin = request.POST.get('humedadAmbienteMin')
    humAmbMax = request.POST.get('humedadAmbienteMax')
    co2Ideal = request.POST.get('co2Ideal')
    co2Min = request.POST.get('co2Min')
    co2Max = request.POST.get('co2Max')
    nivelAguaIdeal = request.POST.get('nivelAguaIdeal')
    nivelAguaMin = request.POST.get('nivelAguaMin')
    nivelAguaMax = request.POST.get('nivelAguaMax')
    filas = request.POST.get('filas')
    columnas = request.POST.get('columnas')

    if nombreObtenido:
        nombre = str(nombreObtenido)
        if len(nombre) > CANTIDAD_CADENA_MAXIMA:
            return "Debe ingresar un nombre menor a 250 caracteres"
    else:
        return "Falta ingresar el nombre del módulo."


    if codigoModuloObtenido:
        try:
            codigoModulo = int(codigoModuloObtenido)
        except Exception as e:
            print(e)
            return "Debe ingresar un numero entero para el código de módulo"
        if codigoModulo < 0:
            return "El código de módulo debe ser mayor a cero"

    else:
        return "Falta ingresar el código para el módulo."

    if idzona:
        idzona = int(idzona)
    else:
        return "Falta seleccionar la zona para el módulo"

    if idzona == CODIGO_GENERAL_COMBO:
        return "Falta seleccionar la zona para el módulo"


    if tempMin == "":
        return "Falta ingresar la temperatura mínima para el módulo."


    if tempMax == "":
        return "Falta ingresar la temperatura máxima para el módulo."


    # if humTierraIdeal == "":
    #     return "Falta ingresar la humedad de la tierra ideal para el módulo."

    if humTierraMin == "":
        return "Falta ingresar la humedad de la tierra mínima para el módulo."

    if humTierraMax == "":
        return "Falta ingresar la humedad de la tierra máxima para el módulo."

    # if humAmbIdeal == "":
    #     return "Falta ingresar la humedad del ambiente ideal para el módulo."

    if humAmbMin == "":
        return "Falta ingresar la humedad del ambiente mínima para el módulo."

    if humAmbMax == "":
        return "Falta ingresar la humedad del ambiente máxima para el módulo."

    #
    # if co2Ideal == "":
    #     return "Falta ingresar la concentración de CO2 ideal para el módulo."


    if co2Min == "":
        return "Falta ingresar la concentración de CO2 mínima para el módulo."


    if co2Max == "":
        return "Falta ingresar la concentración de CO2 máxima para el módulo."

    # if nivelAguaIdeal == "":
    #     return "Falta ingresar el nivel del agua ideal para el módulo."


    if nivelAguaMin == "":
        return "Falta ingresar el nivel del agua mínimo para el módulo."


    if nivelAguaMax == "":
        return "Falta ingresar el nivel del agua máximo para el módulo."


    if filas == "":
        return "Falta ingresar las filas para el módulo."
    else:
        try:
            filas = int(filas)
        except Exception as e:
            print(e)
            return "Debe ingresar un numero entero para el valor de las filas"
        if filas <= 0:
            return "El valor para las filas debe ser mayor a cero"

    if columnas == "":
        return "Falta ingresar las columnas para el módulo."
    else:
        try:
            columnas = int(columnas)
        except Exception as e:
            print(e)
            return "Debe ingresar un numero entero para el valor de las columnas"
        if columnas <= 0:
            return "El valor para las columnas debe ser mayor a cero"


    tempMin = float(tempMin)
    tempMax = float(tempMax)
    if tempMin > tempMax:
        return "La temperatura mínima debe ser menor a la temperatura máxima."

    if tempIdeal != "":
        tempIdeal = float(tempIdeal)
        if (tempIdeal >= tempMin) and (tempIdeal <= tempMax):
            print("Temperatura Ideal Valida")
        else:
            return "La temperatura ideal debe ser un valor entre la mínima y la máxima."
    else:
        tempIdeal = None


    humTierraMax = float(humTierraMax)
    humTierraMin = float(humTierraMin)
    if humTierraMin > humTierraMax:
        return "La humedad de la tierra mínima debe ser menor a la humedad de la tierra máxima."

    if humTierraIdeal != "":
        humTierraIdeal = float(humTierraIdeal)
        if (humTierraIdeal >= humTierraMin) and (humTierraIdeal <= humTierraMax):
            print("Humedad Tierra Ideal Valida")
        else:
            return "La humedad de la tierra ideal debe ser un valor entre el mínimo y el máximo."
    else:
        humTierraIdeal = None


    humAmbMin = float(humAmbMin)
    humAmbMax = float(humAmbMax)
    if humAmbMin > humAmbMax:
        return "La humedad del ambiente mínima debe ser menor a la humedad del ambiente máxima."

    if humAmbIdeal != "":
        humAmbIdeal = float(humAmbIdeal)
        if (humAmbIdeal >= humAmbMin) and (humAmbIdeal <= humAmbMax):
            print("Humedad Ambiente Ideal Valida")
        else:
            return "La humedad del ambiente ideal debe ser un valor entre el mínimo y el máximo."
    else:
        humAmbIdeal = None


    co2Min = float(co2Min)
    co2Max = float(co2Max)
    if co2Min > co2Max:
        return "La concentración de CO2 mínima debe ser menor a la concentración de CO2 máxima."

    if co2Ideal != "":
        co2Ideal = float(co2Ideal)
        if (co2Ideal >= co2Min) and (co2Ideal <= co2Max):
            print("CO2 Ideal Valida")
        else:
            return "La concentración de CO2 ideal debe ser un valor entre el mínimo y el máximo."
    else:
        co2Ideal = None


    nivelAguaMin = float(nivelAguaMin)
    nivelAguaMax = float(nivelAguaMax)
    if nivelAguaMin > nivelAguaMax:
        return "El nivel del agua mínimo debe ser menor al nivel del agua máximo."

    if nivelAguaIdeal != "":
        nivelAguaIdeal = float(nivelAguaIdeal)
        if (nivelAguaIdeal >= nivelAguaMin) and (nivelAguaIdeal <= nivelAguaMax):
            print("Nivel del Agua Ideal Valida")
        else:
            return "EL nivel del agua ideal debe ser un valor entre el mínimo y el máximo."
    else:
        nivelAguaIdeal = None

    idUsuarioObtenido = request.session.get('idUsuarioActual')
    if idUsuarioObtenido == "" or idUsuarioObtenido == None:
        return "Ocurrió un error al tratar de crear la zona. Intente de nuevo en un momento."
    idUsuarioActual = int(idUsuarioObtenido)

    moduloObtenidoBd = None
    if idModulo is None:
        idMax = Modulosemilla.objects.all().aggregate(Max('idmodulo'))['idmodulo__max']
        if idMax is None:
            idModulo = 1
        else:
            idModulo = idMax + 1
        moduloObtenidoBd = Modulosemilla.objects.filter(codigomodulojson=codigoModulo, habilitado=True)

    else:
        moduloObtenidoBd = Modulosemilla.objects.filter(codigomodulojson=codigoModulo, habilitado=True).exclude(idmodulo=idModulo)
        print(moduloObtenidoBd)

    if moduloObtenidoBd.exists():
        return "Ya existe el codigo de modulo. Ingrese un codigo de modulo distinto"

    with transaction.atomic():
        modulo,created = Modulosemilla.objects.update_or_create(
            idmodulo=idModulo, defaults={
            "nombre":nombre,
            "idzona":idzona,
            "codigomodulojson" :codigoModulo,
            "temperaturaideal":tempIdeal,
            "temperaturamin" :tempMin,
            "temperaturamax" :tempMax,
            "humedadtierraideal": humTierraIdeal,
            "humedadtierramin": humTierraMin,
            "humedadtierramax": humTierraMax,
            "humedadambienteideal": humAmbIdeal,
            "humedadambientemin": humAmbMin,
            "humedadambientemax": humAmbMax,
            "concentracionco2ideal":co2Ideal,
            "concentracionco2min":co2Min,
            "concentracionco2max":co2Max,
            "nivelaguaideal": nivelAguaIdeal,
            "nivelaguamin": nivelAguaMin,
            "nivelaguamax": nivelAguaMax,
            "fechacreacion" :datetime.now(),
            "filas":filas,
            "columnas":columnas,
            "habilitado":True,
            "idusuarioauditado":idUsuarioActual}
        )


    return None
    
def paginar(numeroPagina, totalPaginas):
    paginacion = ""
    paginacion += "<button class=\"btn btn-primary\" type=\"button\" disabled>%s</button>" % (numeroPagina)
    cantidadBloques = 1
    bloquesIzquierda = 2
    bloquesDerecha = 2
    if totalPaginas - numeroPagina < bloquesDerecha:
        bloquesIzquierda += bloquesDerecha - (totalPaginas - numeroPagina)
    pagina = numeroPagina - 1
    while pagina > 0 and cantidadBloques < bloquesIzquierda + 1:
        paginacion = "<button class=\"btn btn-default\" type=\"button\" onclick=\"location.href='?page=%s';\">%s</button>" % (pagina, pagina) + paginacion
        pagina -= 1
        cantidadBloques += 1
    pagina = numeroPagina + 1
    while pagina <= totalPaginas  and cantidadBloques < 5:
        paginacion =  paginacion + "<button class=\"btn btn-default\" type=\"button\" onclick=\"location.href='?page=%s';\">%s</button>" % (pagina, pagina)
        pagina += 1
        cantidadBloques +=1
    if numeroPagina > 1:
        paginacion = "<button class=\"btn btn-default\" type=\"button\" onclick=\"location.href='?page=%s';\">Anterior</button>" % (numeroPagina - 1) + paginacion
    else:
        paginacion = "<button class=\"btn btn-default\" type=\"button\" disabled>Anterior</button>" + paginacion
    if numeroPagina < totalPaginas:
        paginacion += "<button class=\"btn btn-default\" type=\"button\" onclick=\"location.href='?page=%s';\">Siguiente</button>" % (numeroPagina + 1)
    else:
        paginacion += "<button class=\"btn btn-default\" type=\"button\" disabled>Siguiente</button>"
    paginacion = "<div class=\"btn-group\" style=\"float: right;\">" + paginacion + "</div>"
    return paginacion

    #paginacion = ""
    #if numeroPagina > 1:
    #    paginacion += '<a href="?page=%s">Anterior</a>' % (numeroPagina - 1)
    #paginacion += '<span class="current"> Página %s de %s </span>' % (numeroPagina, totalPaginas)
    #if numeroPagina < totalPaginas:
    #    paginacion += '<a href="?page=%s">Siguiente</a>' % (numeroPagina + 1)
    #return paginacion

def fotos(request, idModulo, template='app/modulosemilla/fotos.html'):
    fotosPorPagina = 20
    if request.method == 'GET':
        if not 'idUsuarioActual' in request.session:
            return redirect('loginIndex')
        if not 'idInvernadero' in request.session:
            return redirect('escogerInvernadero')
        if not tienepermiso(request, "Ver Modulosemilla"):
            return accesodenegado(request)
        fotosModulo = Foto.objects.filter(idmodulo=idModulo).order_by('-fecharegistro')
        pagina = request.GET.get('page', '1')
        pagina = int(pagina)
        limite = fotosPorPagina * pagina
        offset = limite - fotosPorPagina
        fotosPagina = fotosModulo[offset:limite]
        totalFotos = fotosModulo.count()
        totalPaginas = totalFotos // fotosPorPagina
        if totalFotos % fotosPorPagina != 0:
            totalPaginas += 1
        paginacion = paginar(pagina, totalPaginas)
        context = {
            'nombreUsuario': request.session.get('nomreUsuario'),
            'nombreInvernadero': request.session.get('nombreInvernadero'),
            'fotos': fotosPagina,
            'paginacion': paginacion,
            'modulo': Modulosemilla.objects.get(idmodulo = idModulo)
        }
        return render(request, template, context)


def grabarCronograma(request,idModulo,idCronograma,horaInicio,horaFin):
    horaInicio = str(horaInicio)
    horaFin = str(horaFin)
    temperatura = request.POST.get('temperatura' + horaInicio + horaFin)
    humedadTierra = request.POST.get('humedadtierra' + horaInicio + horaFin)
    humedadAmbiente = request.POST.get('humedadambiente' + horaInicio + horaFin)
    co2 = request.POST.get('co2' + horaInicio + horaFin)
    valorLuz = request.POST.get('luz' + horaInicio + horaFin)
    if valorLuz == "Encendido" :
        luz = True
    else:
        luz = False

    nivelAgua = request.POST.get('nivelagua'+horaInicio+horaFin)

    if idCronograma is None:
        idMax = Cronograma.objects.all().aggregate(Max('idcronograma'))['idcronograma__max']
        if idMax is None:
            idCronograma = 1
        else:
            idCronograma = idMax + 1

    with transaction.atomic():
        cronograma,created = Cronograma.objects.update_or_create(
            idcronograma=idCronograma,idmodulo=idModulo,horainicio=horaInicio,horafin=horaFin, defaults={
            "temperatura":temperatura,
            "humedadtierra":humedadTierra,
            "humedadambiente" :humedadAmbiente,
            "concentracionco2":co2,
            "luz" :luz,
            "nivelagua" :nivelAgua}
        )


    return None

def obtenerCronogramaVacio():
    listaCronogramas = []
    for i in range(0,24):
        cronograma = Cronograma()
        cronograma.idcronograma = None
        cronograma.horainicio = i
        cronograma.horafin = i+1
        cronograma.temperatura = 0
        cronograma.humedadambiente = 0
        cronograma.humedadtierra = 0
        cronograma.concentracionco2 = 0
        cronograma.luz = False
        cronograma.nivelagua = 0
        listaCronogramas.append(cronograma)
    return listaCronogramas

def cronograma(request, idModulo):
    template = 'app/modulosemilla/cronograma.html'
    listaRegistrosCronograma = Cronograma.objects.filter(idmodulo=idModulo)
    
    if listaRegistrosCronograma:
        listaRegistrosCronograma = listaRegistrosCronograma.order_by('horainicio')
    else:
        listaRegistrosCronograma = obtenerCronogramaVacio()

    context = {'listaRegistrosCronograma':listaRegistrosCronograma,'nombreUsuario': request.session.get('nomreUsuario'),
               'nombreInvernadero': request.session.get('nombreInvernadero')}

    if request.method == 'POST':
        if "b_aceptar" in request.POST:
            if not 'idUsuarioActual' in request.session:
                return redirect('loginIndex')
            if not 'idInvernadero' in request.session:
                return redirect('escogerInvernadero')
            if not tienepermiso(request, "Editar Modulosemilla"):
                return accesodenegado(request)
            print(request.POST)
            for registro in listaRegistrosCronograma:
                try:
                    grabarCronograma(request, idModulo,registro.idcronograma, registro.horainicio, registro.horafin)
                except Exception as e:
                    print(e)
            listaRegistrosCronograma = Cronograma.objects.filter(idmodulo=idModulo)
            if listaRegistrosCronograma:
                listaRegistrosCronograma = listaRegistrosCronograma.order_by('horainicio')
                context['listaRegistrosCronograma'] = listaRegistrosCronograma

        if "b_cancelar" in request.POST:
            return redirect('moduloSemillaDetalle',idModulo = idModulo)

    ##Supongo q aqui es donde se renderiza si request.method == GET, no se, q1 revisalo ctmr
    if not 'idUsuarioActual' in request.session:
        return redirect('loginIndex')
    if not 'idInvernadero' in request.session:
        return redirect('escogerInvernadero')
    if not tienepermiso(request, "Ver Modulosemilla"):
        return accesodenegado(request)
    return render(request, template, context)

