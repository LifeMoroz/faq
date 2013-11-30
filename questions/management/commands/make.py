import os

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


def get(key, default=None):
    try:
        val = getattr(settings, key, default)
    except AttributeError:
        val = None
    if not val:
        if default is None:
            raise CommandError('settings.%s not found' % key)
        val = default
    return val


conf = {
    '$db_password$': settings.DATABASES['default']['PASSWORD'],
    '$db_user$': settings.DATABASES['default']['USER'],
    '$db$': settings.DATABASES['default']['NAME'],
    '$root$': get('BASE_DIR'),
    '$backend_port$': get('BACKEND_PORT'),
    '$tornado_port$': get('TORNADO_PORT'),
    '$redis_port': get('REDIS_PORT'),
    '$host$': get('HOST'),
}


class Command(BaseCommand):
    help = 'Updates configuration files'

    def handle(self, *args, **options):
        template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
        templates = os.listdir(template_dir)
        config_directory = os.path.join(get('BASE_DIR'), 'conf')

        for template in templates:
            self.stdout.write('Generating %s' % template)
            template_file = open(os.path.join(template_dir, template)).read()
            config_file = open(os.path.join(config_directory, template), 'w')
            for key, replacement in conf.items():
                template_file = template_file.replace(key, str(replacement))
            config_file.write(template_file)
            config_file.close()
        for key, replacement in conf.items():
            self.stdout.write('{0:<15} {1}'.format(key.replace('$', ''), replacement))
        self.stdout.write('Successfully generated settings')