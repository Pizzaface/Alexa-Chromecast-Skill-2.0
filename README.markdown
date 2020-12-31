# Alexa Chromecast Skill (Versión en español)

Permite a Alexa de Amazon controlar Google Chromecast

Esta habilidad o skill te permite controlar uno o varios Chromecast en diferentes habitaciones. Cada dispositivo de Alexa puede ser configurado para controlar una habitación diferente. 

Esto se hace emparejando el nombre de la habitación con el nombre de su dispositivo Chromecast. Por ejemplo, si el nombre de su Chromecast es: "Dormitorio principal", entonces configura la habitación de Alexa para controlar el "Dormitorio principal"

El siguiente comando detiene el Chromecast del Dormitorio Principal: 
> Alexa, pídele a Chromecast que pause

También puedes controlar otra habitación diciendo algo como:
> Alexa, pide a Chromecast que pause en Sala de Estar

Para cambiar la habitación que un dispositivo particular de Alexa controla puedes decir:
> Alexa, pídele a Chromecast que cambie de habitación

Aquí hay algunos ejemplos de comandos de voz:

> Alexa, dile a Chromecast que empiece a reproducir

> Alexa, dile a Chromecast que ponga canciones de Macklemore

> Alexa, dile a Chromecast que ponga la lista de reproducción de Maroon 5

> Alexa, dile a Chromecast que ponga el tráiler de Matrix

> Alexa, dile a Chromecast que ponga el volumen a 5

> Alexa, dile a Chromecast que se detenga

O,

> Alexa, pídele al Chromecast de la Sala de Estar que pare

> Alexa, pide a Chromecast que siga en Sala de Estar

## Cómo funciona

Las skills de Alexa se ejecutan en la nube, pero esta skill debe estar en su red local para controlar el Chromecast. Esta habilidad implementa un enfoque híbrido: el comando es manejado por Alexa en AWS(Amazon Web Services), que envía una notificación a su servidor local.

El componente Lambda está en `src/lambda`, y el componente local está en `src/local`.

![Visión general de arquitectura](docs/diagrama.jpg "Visión general de arquitectura")

Tanto el Chromecast como el Raspberry Pi (o lo que sea con lo que se ejecute el gestor de notificaciones locales) **DEBE** estar en la misma red para que el Chromecast pueda ser reconocido.

## Dependencias

La instalación requiere un entorno UNIX con:

- BASH
- Python 3.7
- [Pip](https://pip.pypa.io/en/stable/installing/)

## Configuración e instalación

### Construir la función lambda de AWS
1. Crea una cuenta de [Amazon Web Services](http://aws.amazon.com/)
2. Ejecuta aws-setup.sh para crear un Rol, Función Lambda y SNS Topic. (*Se ejecutará `aws configure`, así que ten un id de clave y una clave de acceso a mano*)
### Configurar la Skill de Alexa
3. Ve a [ASK Console](developer.amazon.com/alexa/console/ask) y elige "Create Skill"
4. Selecciona "Custom" y "Provision your own", y luego haga clic en "Create skill". En la pantalla de la plantilla escoge la plantilla "Hello World Skill"
5. Haz clic en "Interaction Model" en el menú de la izquierda, y luego en "JSON Editor"
6. Copia y pega el contenido de `config/interaction_model.json` en el editor, luego haga clic en "Save Model"
7. Haz clic en "Endpoint" en el menú de la izquierda. Introduce el ARN de la función Lambda que has obtenido al ejecutar aws-setup.sh. Y después haz clic en "Save Endpoints"
8. Haz clic en "Invocation" en el menú de la izquierda. Y haz clic en "Build Model"
9. Haz clic en la pestaña "Test". Prueba cómo funciona.
### Instalar la aplicación local que controla los Chromecast
10. Instala las dependencias locales con `sudo pip3 install -r ./src/local/requirements.txt`
11. Ejecuta `./start.sh` para iniciar el receptor, o `./docker-start.sh` para operar en una sesión interactiva de docker. O `./docker-start.sh -d` para ejecutar como un servicio.
El servicio intenta comunicar con AWS SNS usando UPNP. Si UPNP está deshabilitado en tu red, puedes especificar un puerto. `./start.sh -p 30000`
Para ver otras opciones ejecuta `./start.sh -h` o `./docker-start.sh -h`.

Cuando se ejecute deberías ver algo como lo siguiente:
```
2020-12-30 11:10:02,484 - root - INFO - Iniciando receptor de Alexa Chromecast...
2020-12-30 11:10:02,498 - local.ChromecastSkill - INFO - Buscando Chromecast...
2020-12-30 11:10:07,618 - pychromecast - INFO - Querying device status
2020-12-30 11:10:07,789 - pychromecast - INFO - Querying device status
2020-12-30 11:10:07,998 - local.ChromecastSkill - INFO - Se ha descubierto Dormitorio principal
2020-12-30 11:10:08,159 - local.ChromecastSkill - INFO - Se ha descubierto Habitación Fernando
2020-12-30 11:10:08,389 - local.ChromecastSkill - INFO - 2 Chromecasts descubiertos
2020-12-30 11:10:10,475 - botocore.credentials - INFO - Found credentials in environment variables.
2020-12-30 11:10:12,684 - local.SkillSubscriber - INFO - Escuchando a http://93.114.157.209:38523
2020-12-30 11:10:12,717 - local.SkillSubscriber - INFO - Suscribiéndose a los comandos de Alexa...
2020-12-30 11:10:13,603 - local.SkillSubscriber - INFO - Confirmación de subscripción recibida...
2020-12-30 11:10:13,913 - local.SkillSubscriber - INFO - Subscrito.

```
### Por último
12. Di "Alexa abre Chromecast", y después "Ayuda"

La skill te enseñará cómo se puede utilizar.

### Ejemplo de Shell o intérprete de comandos

  `./start.sh`

### Docker

El suscriptor de la Skill se puede ejecutar con docker:

`./docker-start.sh` - para una sesión interactiva

`./docker-start.sh -d` - para ejecutar como un servicio

### Variables de entorno

El suscriptor de la skill (local) utiliza estas variables de entorno:

- **AWS_SNS_TOPIC_ARN** - ARN de AWS SNS Topic (se puede encontrar en el archivo `.env` después de ejecutar `aws-setup.sh`)
- **AWS_ACCESS_KEY_ID** - Clave de acceso de usuario de AWS
- **AWS_SECRET_ACCESS_KEY** - Clave de acceso secreta de AWS
- **AWS_DEFAULT_REGION** - Región de AWS Lambda y SNS (ej. eu-west-1)

Si has ejecutado `aws configure`, no necesitarás configurar AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, o AWS_DEFAULT_REGION.

## Scripts

### aws-setup.sh

Establece un entorno AWS para la Skill de Alexa:

1. Crea un rol IAM para Alexa (con permisos para el SNS)
2. Crea un SNS Topic para comunicarse a través de él
3. Crea un almacén de S3 persistente para la habitación seleccionada a la que el dispositivo Alexa está accediendo
4. Crea una función Lambda

### build-lambda-bundle.sh

Crea un lambda-bundle.zip, que puede subirse a una función Lambda de AWS.

### aws-update-lambda.sh

Ejecuta build-lambda-bundle y automáticamente sube el paquete a AWS Lambda.


## FAQ

### "No Chromecasts found"
Cuando el servicio local comienza a buscar Chromecast en la red. Si no se encuentran Chromecast, se saldrá. Para solucionar esto, debes confirmar que el Chromecast está encendido y funcionando, asegúrate de que puedes acceder a él desde tu teléfono, y asegúrate de que todo está en la misma red. Para depurar, se proporciona una herramienta para buscar y listar los Chomecast encontrados en `./search-chromecasts` (asegúrate de que se pueda ejecutar con `chmod +x ./search-chromecasts`).

### El receptor local no se suscribe
Si el receptor local no se suscribe (no hay mensajes de suscripción o un error) entonces los Chromecast no recibirán comandos de Alexa Por defecto, el receptor local utiliza UPNP y un puerto dinámico para establecer una conexión externa, que puede ser anulada si es necesario.
1. Comprueba que UPNP está habilitado/permitido en su red
2. Si UPNP no está habilitado o no funciona, intenta especificar manualmente un puerto y asegúrate de que su cortafuegos/rúter esté configurado para permitir el acceso externo a este puerto. por ejemplo, para usar el puerto 30000 ejecuta `./start.sh -p 30000` o `./docker-start.sh -p 30000`
3. Entra en la consola AWS y comprueba que el SNS Topic está instalado, y comprueba los registros de Cloud Watch para tu función lambda por si hay algún error.

### Alexa tuvo un error al lanzar la skill o al procesar un comando
1. Intenta reemplazar la skill lambda con `./aws-update-lambda.sh`
2. Si esto no funciona, ve a la consola AWS y comprueba los registros de CloudWatch asociados a la función lambda.

### Alexa aceptó el comando pero no parece que funcione.
1. Revisa el output del receptor local, debería mostrar el comando recibido y cualquier error que se haya encontrado
2. Para comprobar los registros del servicio de docker, ejecuta algo como `docker logs alexa_chromecast --since=30m`, que te mostrará los registros de los últimos 30 minutos
