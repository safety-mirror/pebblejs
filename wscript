#
# This file is the default set of rules to compile a Pebble application.
#
# Feel free to customize this to your needs.
#
import os.path

top = '.'
out = 'build'


def options(ctx):
    ctx.load('pebble_sdk')

def configure(ctx):
    """
    This method is used to configure your build. ctx.load(`pebble_sdk`) automatically configures
    a build for each valid platform in `targetPlatforms`. Platform-specific configuration: add your
    change after calling ctx.load('pebble_sdk') and make sure to set the correct environment first.
    Universal configuration: add your change prior to calling ctx.load('pebble_sdk').
    """
    ctx.env.CFLAGS = ['-std=c11',
                      '-fms-extensions',
                      '-Wno-address',
                      '-Wno-type-limits',
                      '-Wno-missing-field-initializers']
    ctx.load('pebble_sdk')

    for _, env in ctx.all_envs.iteritems():
        if '-std=c99' in env.CFLAGS:
            env.CFLAGS.remove('-std=c99')

    ctx.find_program('coffee', var='COFFEE', path_list='node_modules/.bin')

def build(ctx):
    ctx.load('pebble_sdk')

    build_worker = os.path.exists('worker_src')
    binaries = []

    cached_env = ctx.env
    for platform in ctx.env.TARGET_PLATFORMS:
        ctx.env = ctx.all_envs[platform]
        ctx.set_group(ctx.env.PLATFORM_NAME)
        app_elf = '{}/pebble-app.elf'.format(ctx.env.BUILD_DIR)
        ctx.pbl_program(source=ctx.path.ant_glob('src/**/*.c'), target=app_elf)

        if build_worker:
            worker_elf = '{}/pebble-worker.elf'.format(ctx.env.BUILD_DIR)
            binaries.append({'platform': platform, 'app_elf': app_elf, 'worker_elf': worker_elf})
            ctx.pbl_worker(source=ctx.path.ant_glob('worker_src/**/*.c'), target=worker_elf)
        else:
            binaries.append({'platform': platform, 'app_elf': app_elf})
    ctx.env = cached_env

    ctx.set_group('bundle')
    coffee_nodes = ctx.path.ant_glob('src/js/**/*.coffee')
    for coffee_node in coffee_nodes:
        ctx(rule="../${COFFEE} -c ${SRC}",
            source=coffee_node,
            target=coffee_node.change_ext('.js'),
            name='coffee',
            color='GREEN')
    ctx.pbl_bundle(binaries=binaries,
                   js=ctx.path.ant_glob(['package.json', 'src/js/**/*.js', 'src/js/**/*.json']),
                   js_entry_file='src/js/app.js')
