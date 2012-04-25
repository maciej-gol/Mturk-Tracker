import os
from os.path import join as pjoin
import json
from fabric.colors import red, yellow
from fabric.api import abort, task, env, hide, settings, sudo, cd
from fabric.contrib.console import confirm_or_abort

from modules import nginx, supervisor, postgresql
from modules.database import (ensure_database, ensure_user, ensure_language)
from modules.virtualenv import (update_virtualenv, create_virtualenv,
    setup_virtualenv)
from modules.utils import (show, put_file_with_perms,
    dir_exists, PROPER_SUDO_PREFIX as SUDO_PREFIX, cget, cset, print_context,
    run_django_cmd, upload_template_with_perms, local_files_dir, get_boolean,
    install_without_prompt, create_target_directories)


PARENT_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_CONF_FILE = pjoin(PARENT_DIR, 'target_defs', 'defaults.json')


def prep_apt_get():
    show(yellow("Updating and fixing apt-get."))
    with settings(hide("stdout", "running"), sudo_prefix=SUDO_PREFIX):
        sudo("apt-get update")
    with settings(sudo_prefix=SUDO_PREFIX):
        sudo("apt-get -f -y install")


def install_system_requirements():
    """Installs packages included in system_requirements.txt.
    This is done before fetch, thus the file is taken from *local* storage.
    """
    reqs = cget('system_requirements')
    if reqs:
        for req in reqs:
            requirements = pjoin(local_files_dir("requirements"), req)
            show(yellow("Processing system requirements file: %s" %
                    requirements))
            with open(requirements) as f:
                r = ' '.join([f.strip() for f in f.readlines()])
                name = 'requirements: {0}'.format(r)
                with settings(warn_only=True, sudo_prefix=SUDO_PREFIX):
                    install_without_prompt(r, name, silent=False)


def prepare_global_env():
    """Ensure global settings - one time only."""
    prep_apt_get()
    install_system_requirements()
    setup_ssh()
    setup_virtualenv()
    nginx.provision()


def setup_ssh():
    """Uploads ssh from the local folder specified in config."""
    user = cget("user")
    ssh_target_dir = cget("ssh_target")

    # Ensure SSH directory is created with proper perms.
    create_target_directories([ssh_target_dir], "700", user)

    # Upload SSH config and keys.
    # TODO: Add copying files from remote folder (upload_ssh_keys_from_local).
    if cget('upload_ssh_keys_from_local') or True:
        files = cget('ssh_files')
        show(yellow("Uploading SSH configuration and keys"))
        for name in files:
            show(u"File: {0}".format(name))
            local_path = pjoin(local_files_dir("ssh"), name)
            remote_path = pjoin(ssh_target_dir, name)
            put_file_with_perms(local_path, remote_path, "600", user, user)
    else:
        # Remoty copying of files
        raise Exception('Not implemented!'
            ' Please set upload_ssh_keys_from_local to True!')


def prepare_target_env():
    """Prepare all things needed before source code deployment."""
    user = cget("user")
    project_dir = cget("project_dir")

    # Ensure we have database and user set up.
    show(yellow("Setting database up"))
    ensure_user(cget("db_user"), cget("db_password"))
    ensure_database(cget("db_name"), cget("db_user"))
    ensure_language(cget("db_name"), 'plpgsql')

    # Ensure proper directory structure.
    create_target_directories([project_dir], '755', user)

    dirs = ["code", "logs", "logs/old", "misc", "virtualenv",
        "media", "static", "scripts", "services"]
    dirs = [pjoin(project_dir, d) for d in dirs]
    create_target_directories(dirs, "755", user)

    nginx.configure()
    postgresql.configure()

    # Create Virtualenv if not present.
    create_virtualenv()


def fetch_project_code():
    """Fetches project code from Github.
        If specified, resets state to selected branch or commit (from context).
    """
    branch = cget("branch")
    commit = cget("commit")
    project_dir = cget("project_dir")
    repo_dir = pjoin(project_dir, "code")
    url = cget("source_url")
    user = cget("user")
    if commit:
        rev = commit
    else:
        rev = "origin/%s" % (branch or "master")

    with settings(sudo_prefix=SUDO_PREFIX):
        if not dir_exists(pjoin(repo_dir, ".git")):
            show(yellow("Cloning repository following: %s"), rev)
            sudo("git clone %s %s" % (url, repo_dir), user=user)
            with cd(repo_dir):
                sudo("git reset --hard %s" % rev, user=user)
        else:
            show(yellow("Updating repository following: %s"), rev)
            with cd(repo_dir):
                sudo("git fetch origin", user=user)  # Prefetch changes.
                sudo("git clean -f", user=user)  # Clean local files.
                sudo("git reset --hard %s" % rev, user=user)


def upload_settings_files():
    """Uploads target specific (templated) settings files.
        If specified also uploads user supplied locals.py.

        *Warning*: Settings are uploaded from your local template file.
        Make sure to have proper branch/revision checked out.
    """
    base_dir = cget("base_dir")
    user = cget("user")
    locals_path = cget("locals_path")

    show(yellow("Uploading Django settings files."))
    # This is Template context not the deployment context.
    # A split should happen some time.
    context = dict(env["ctx"])
    context
    # Upload main settings and ensure permissions.
    source = pjoin(local_files_dir("django"), "settings_template.py")
    destination = pjoin(base_dir, "settings", "%s.py" % cget("settings_name"))
    upload_template_with_perms(source, destination, context, mode="644",
        user=user, group=user)

    # We could be deploying from different directory.
    # Try our best to find correct path.
    # First - direct, absolute match.
    if not os.path.isfile(locals_path):
        # Try relative to deployment directory.
        this_dir = os.path.dirname(os.path.abspath(__file__))
        locals_path = pjoin(this_dir, locals_path)
        if not os.path.isfile(locals_path):  # :((
            msg = u"Warning: Specified local settings path is incorrect: {0}."
            show(red(msg.format(locals_path)))
            confirm_or_abort(red("\nDo you want to continue?"))
            locals_path = None

    # Upload user supplied locals if present.
    if locals_path:
        show(yellow("Uploading your custom local settings files."))
        destination = pjoin(base_dir, "settings", "local.py")
        put_file_with_perms(locals_path, destination, mode="644", user=user,
            group=user)


def collect_staticfiles():
    """Quietly runs `collectstatic` management command"""
    show(yellow("Collecting static files"))
    run_django_cmd("collectstatic", args="--noinput")


def compile_messages():
    """Runs `compilemessages` management command"""
    show(yellow("Compiling translation messages"))
    run_django_cmd("compilemessages")


def sync_db():
    """Quietly runs `syncdb` management command"""
    show(yellow("Synchronising database"))
    run_django_cmd("syncdb", args="--noinput")
    run_django_cmd("migrate", args="--noinput")


def configure_services():
    """Ensures correct init and running scripts for services are installed."""
    supervisor.configure()
    postgresql.configure()


def reload_services():
    """Reloads previously configured services"""
    supervisor.reload()
    nginx.reload()


def set_instance_conf():
    """Compute all instance specific paths and settings.
    Put *all* settings computation login here.
    """
    # System
    cset("user", env["user"])

    # Common project settings.
    cset("prefix", cget("default_prefix"))
    cset("project_name", "%s-%s" % (cget("prefix"), cget("instance")))
    cset("project_dir", pjoin(cget("projects_dir"), cget("project_name")))
    cset("virtualenv_dir", pjoin(cget("project_dir"), "virtualenv"))
    cset("deployment_files", pjoin(cget("project_dir"), "code", "deployment",
        "files"))
    cset('settings_full_name', '.'.join([cget('project_inner'), 'settings',
        cget('settings_name')]))
    cset('service_dir', pjoin(cget("project_dir"), "services"))

    # Directory with manage.py script.
    cset("manage_py_dir", pjoin(cget("project_dir"), "code"))
    cset("base_dir", pjoin(cget("project_dir"), "code", cget("project_inner")))
    cset("log_dir", pjoin(cget("project_dir"), "logs"))

    # Database settings
    cset("db_name", "%s_%s" % (cget("prefix"), cget("instance")))
    cset("db_user", cget("db_name"))
    cset("db_password", cget("db_user"))

    # SSH
    user = cget("user")
    cget("ssh_target") or cset("ssh_target", "/home/%s/.ssh" % user)


def load_config_files(conf_file, default_conf=DEFAULT_CONF_FILE,
        use_default=True):
    """Populates env['ctx'] with settings from the provided and default files.
        ``conf_file`` - configuration file to use
        ``default_conf`` - default configuration file used as a base,
                           global default is 'target_defs/defaults.json'
        ``use_defaults`` - allows to avoid using the defaults file
    """
    # Try loading configuration from JSON file.
    if conf_file:
        with open(conf_file) as f:
            fctx = json.load(f)
        show(yellow("Using configuration from: %s"), conf_file)
    else:
        show(yellow("Using sane defaults"))
        fctx = {}

    # Load the default configuration if exists
    if use_default:
        try:
            with open(default_conf) as f:
                dctx = json.load(f)
            msg = "Using default configuration from: %s"
            show(yellow(msg), default_conf)
        except Exception as e:
            show(yellow("Default conf file error! %s"), e)
            confirm_or_abort(red("\nDo you want to continue?"))
            dctx = {}
    dctx.update(fctx)
    env["ctx"] = dctx
    return dctx


def update_args(ctx, instance, branch, commit, locals_path, requirements,
        setup_environment):
    """Check args and update ctx."""
    # Do the sanity checks.
    instance = cset("instance", instance)
    if not instance or not instance.isalnum():
        abort("You have to specify a proper alphanumeric instance name!")
    if branch is not None and commit is not None:
        abort("You can only deploy specific commit OR specific branch")
    commit and cset("commit", commit, force=True)
    branch and cset("branch", branch, force=True)
    cset("locals_path", locals_path)
    cset("requirements", get_boolean(requirements))
    cset("setup_environment", get_boolean(setup_environment))
    return ctx


@task
def deploy(conf_file=None, instance=None, branch=None, commit=None,
        locals_path=None, setup_environment=False, requirements=True):
    u"""Does a full deployment of the project code.
        You have to supply an ``instance`` name (the name of deployment
        target in colocation environment).

        ``conf_file`` should be a path to a properly formatted JSON
        configuration file that will override default values.

        If ``locals_path`` is specified this file is used as
        a local settings file.
        Arguments ``commit`` and ``branch`` can be used to deploy
        some specific state of the codebase.
    """
    # Get file configuration and update with args
    env['ctx'] = {}

    ctx = load_config_files(conf_file)
    ctx = update_args(ctx, instance, branch, commit, locals_path,
        requirements, setup_environment)

    # Fill instance context.
    set_instance_conf()
    print_context()

    # Give user a chance to abort deployment.
    confirm_or_abort(red("\nDo you want to continue?"))
    # Prepare server environment for deployment.
    show(yellow("Preparing project environment"))
    if get_boolean(setup_environment):
        prepare_global_env()
    prepare_target_env()

    # Fetch source code.
    fetch_project_code()

    if get_boolean(requirements):
        # Update Virtualenv packages.
        update_virtualenv()

    # Upload target specific Django settings.
    upload_settings_files()
    # Collect static files.
    collect_staticfiles()
    # Compile translation messages.
    compile_messages()
    # Update database schema.
    sync_db()
    # Uploads settings and scripts for services.
    configure_services()
    # Reload services to load new config.
    reload_services()
