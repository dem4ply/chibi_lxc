import os
import logging
from chibi.atlas import Chibi_atlas
from chibi.file import Chibi_path
from chibi_command import lxc
from chibi_command.rsync import Rsync
from chibi_hybrid import Class_property
from chibi_lxc.file.config import Chibi_lxc_config
from chibi_donkey.donkey import Donkey
from chibi.config import configuration


donkey = Donkey( '.' )


logger = logging.getLogger( 'chibi_lxc.container' )


class Not_exists_error( Exception ):
    pass


class Creation_error( Exception ):
    pass

class Destruction_error( Exception ):
    pass


class Container_meta( type ):
    def __new__( cls, clsname, bases, clsdict ):
        clsobj = super().__new__( cls, clsname, bases, clsdict )
        if isinstance( clsobj.provision_folders, dict ):
            for k, v in clsobj.provision_folders.items():
                clsobj.provision_folders[k] = Chibi_path( v )


        containers = list(
            filter( lambda x: issubclass( x, Container ), bases ) )
        containers_with_scripts = filter( lambda x: x.scripts, containers )
        _scripts = (
            s for c in containers_with_scripts for s in c.scripts )
        _set_scripts = set()
        scripts = []
        for script in _scripts:
            if script not in _set_scripts:
                scripts.append( script )
                _set_scripts.add( script )

        if clsobj.scripts:
            for script in clsobj.scripts:
                if script not in _set_scripts:
                    scripts.append( script )
                    _set_scripts.add( script )
            clsobj.scripts = tuple( scripts )
        else:
            clsobj.scripts = scripts

        names = ( c.name for c in containers )
        equal_names = ( clsobj.name == name for name in names )
        if any( equal_names ):
            clsobj.name = clsobj.__name__

        return clsobj


class Container( metaclass=Container_meta ):
    name = "unset"
    distribution = 'centos'
    arch = 'amd64'
    version = '7'

    provision_root = Chibi_path( 'home/chibi/provision/' )
    provision_folders = Chibi_atlas()
    scripts = None

    env_vars = Chibi_atlas( {
        'PROVISION_PATH': '/' + str( provision_root ) + 'scripts'
    } )

    @Class_property
    def info( cls ):
        result = lxc.Info.name( cls.name ).run()
        if result:
            result.result
        else:
            raise Not_exists_error( result.error )
        return result

    @Class_property
    def config( cls ):
        if os.getuid() != 0:
            return Chibi_path(
                f'~/.local/share/lxc/{cls.name}/config',
                chibi_file_class=Chibi_lxc_config )
        return Chibi_path(
            f'/var/lib/lxc/{cls.name}/config',
            chibi_file_class=Chibi_lxc_config )

    @Class_property
    def exists( cls ):
        result = lxc.Info.name( cls.name ).run()
        return bool( result )

    @Class_property
    def root( cls ):
        if os.getuid() != 0:
            return Chibi_path( f'~/.local/share/lxc/{cls.name}/rootfs' )
        return Chibi_path( f'/var/lib/lxc/{cls.name}/rootfs' )

    @Class_property
    def provision_folder( cls ):
        return Chibi_atlas( {
            k: cls.root + '..' + k
            for k, v in cls.provision_folders.items() } )

    @Class_property
    def script_folder( cls ):
        return '/' + cls.provision_root + 'scripts/'

    @Class_property
    def is_running( cls ):
        return cls.info.is_running

    @classmethod
    def create( cls ):
        template = lxc.Create.name( cls.name ).template( 'download' )
        template = template.parameters(
            '-d', cls.distribution, '-r', cls.version,
            '--arch', cls.arch )
        result = template.run()
        if not result:
            raise Creation_error(
                "un error en la creacion del contenedor"
                f" '{result.return_code}' revise los output" )
        return result

    @classmethod
    def start( cls, daemon=True ):
        command = lxc.Start.name( cls.name )
        if daemon:
            command.daemon()
        result = command.run()
        return result

    @classmethod
    def stop( cls ):
        command = lxc.Stop.name( cls.name )
        result = command.run()
        return result

    @classmethod
    def destroy( cls, stop=False ):
        if cls.is_running and stop:
            cls.stop()
        template = lxc.Destroy.name( cls.name )
        result = template.run()
        if not result:
            raise Destruction_error(
                "un error en la destruscion del contenedor"
                f" '{result.return_code}' revise los output" )
        return result

    @classmethod
    def provision( cls ):
        config = cls.config.open().read()
        hosts = configuration.chibi_lxc.hosts

        for k, v in cls.provision_folders.items():
            real_folder = cls.provision_folder[k]
            mount = (
                f"{real_folder}  {cls.provision_root}/{k} "
                "none bind,create=dir 0 0" )

            if "mount" not in config.lxc:
                config.lxc.mount = Chibi_atlas( entry=[] )
            entries = config.lxc.mount.entry
            if not isinstance( entries, list ):
                entries = [ entries ]
            for entry in entries:
                if entry == mount:
                    break
            else:
                entries.append( mount )
                cls.config.open().write( config )
                config = cls.config.open().read()

            if not real_folder.exists:
                real_folder.mkdir()
            if v.is_a_folder and not v.endswith( '/' ):
                v = str( v ) + '/'
            if not real_folder.exists:
                real_folder.mkdir()
            Rsync.clone_dir().human().verbose().run(
                v, real_folder )
            if hosts and hosts.exists:
                hosts.copy( real_folder + 'hosts' )

    @classmethod
    def attach( cls, script, *args ):
        attach = lxc.Attach.name( cls.name )
        for k, v in cls.env_vars.items():
            attach.set_var( k, v )
        command, script = cls._prepare_script( script )
        return attach.run( command, cls.script_folder + script, *args )

    @classmethod
    def run_scripts( cls ):
        for script in cls.scripts:
            if isinstance( script, tuple ):
                args = cls._prepare_script_arguments( *script[1:] )
                script = script[0]
                result = cls.attach( script, *args )
            else:
                result = cls.attach( script )
            if not result:
                logger.error(
                    f"fallo el script '{script}' se regreso el codigo "
                    f"{result.return_code}" )
                return result

    @classmethod
    def _prepare_script_arguments( cls, *args ):
        result = []
        for a in args:
            if isinstance( a, str ):
                if a.startswith( 'cls.' ):
                    a = a[4:]
                    result.append( getattr( cls, a ) )
                    continue
            result.append( a )
        return result

    @staticmethod
    def _prepare_script( script ):
        if script.endswith( 'py' ):
            return 'python3', script
        return 'bash', script
