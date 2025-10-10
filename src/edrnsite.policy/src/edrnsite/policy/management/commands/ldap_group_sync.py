# encoding: utf-8

'''🧬 EDRN Site: LDAP group sync.'''

from django.core.management.base import BaseCommand, CommandError
from django_auth_ldap.backend import LDAPBackend
from django.contrib.auth.models import Group


class Command(BaseCommand, LDAPBackend):
    help = 'Sync LDAP groups → Django groups'

    def handle(self, *args, **options):
        # Django has a limit of the max length of a group name so we'll have to truncate our super-long LDAP
        # group names from EDRN, le sigh
        limit = Group.name.field.max_length

        # Assuming BIND_DN is of the form `uid=USERID,…other digraph edges…`:
        username = self.settings.BIND_DN.split(',')[0][4:]
        user = self.authenticate(request=None, username=username, password=self.settings.BIND_PASSWORD)
        if user is None:
            raise CommandError(f'Could not authenticate {username} with LDAP; cannot continue!')

        # This will fail with the `service` account because it exceeds the 500 size limit, and
        # there seems to be no way to paginate with django-auth-ldap.
        #
        # We really need to clean up the older groups.
        for group_pair in self.settings.GROUP_SEARCH.execute(user.ldap_user.connection):
            group_name = group_pair[1]['cn'][0][:limit]
            Group.objects.get_or_create(name=group_name)
