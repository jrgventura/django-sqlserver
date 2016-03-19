import os.path
import subprocess
import itertools

django_repo_url = 'https://github.com/django/django.git'
mssql_repo_url = 'https://bitbucket.org/Manfre/django-mssql.git'
python_versions = ['2.7', '3.3', '3.4', '3.5']
django_versions = ['1.8', '1.9']
pytds_versions = ['1.8.2']
tests = ['aggregation',
         'aggregation_regress',
         'inspectdb',
         'introspection',
         'm2m_and_m2o',
         'migrations',
         'migrations2',
         'model_fields',
         'model_regress',
         'multiple_database',
         'nested_foreign_keys',
         'null_fk',
         'null_fk_ordering',
         'null_queries',
         'ordering',
         'pagination',
         #'queries',  # failing
         'raw_query',
         #'schema',  # failing
         'select_for_update',
         'select_related',
         'select_related_onetoone',
         'select_related_regress',
         'servers',
         #'timezones',  # failing
         'transactions',
         'update',
         'update_only_fields',
         ]
extra_tests = {
    '1.8': [
    ],
    '1.9': [
        'transaction_hooks',
    ],
}
exclude_tests = ['aggregation.tests.ComplexAggregateTestCase.test_expression_on_aggregation']

# TODO find python
python_exe = 'python2.7'
virtualenv_exe = 'virtualenv'
pip_exe = 'pip'
git_exe = 'git'

build_folder = 'build'


def run_tests(django_ver, pytds_ver):
    root = os.getcwd()
    venv_folder = os.path.join(build_folder, 'venv')

    if not os.path.isdir(venv_folder):
        # using system-site-packages to get pywin32 package which is not installable via pip
        subprocess.check_call([virtualenv_exe, venv_folder, '--system-site-packages', '--python', python_exe])

    venv_pip = os.path.join(venv_folder, 'bin', 'pip')
    venv_python = os.path.join(venv_folder, 'bin', 'python')

    django_branch = 'stable/{}.x'.format(django_ver)

    django_folder = os.path.join(venv_folder, 'src', 'django')

    # cloning Django repository
    if not os.path.isdir(django_folder):
        subprocess.check_call([git_exe, 'clone', django_repo_url, django_folder])

    # update Django repository
    subprocess.check_call([git_exe, 'pull'], cwd=django_folder)

    # select version branch in Django repo
    subprocess.check_call([git_exe, 'checkout', '--force', django_branch], cwd=django_folder)

    # apply patch on Django
    patch = os.path.join(root, 'django{}-patch.txt'.format(django_ver))
    subprocess.check_call([git_exe, 'apply', patch], cwd=django_folder)

    # install Django test requirements
    subprocess.check_call([venv_pip, 'install', '-r', os.path.join(django_folder, 'tests', 'requirements', 'py2.txt')])

    mssql_folder = os.path.join(venv_folder, 'src', 'django-mssql')
    if not os.path.isdir(mssql_folder):
        subprocess.check_call([git_exe, 'clone', mssql_repo_url, mssql_folder])

    # update django-mssql repo
    subprocess.check_call([git_exe, 'pull'], cwd=mssql_folder)
    subprocess.check_call([git_exe, 'checkout', '--force'], cwd=mssql_folder)

    # apply patch on django-mssql
    patch = os.path.join(root, 'django-mssql-patch.txt')
    subprocess.check_call([git_exe, 'apply', patch], cwd=mssql_folder)

    # install pytds
    subprocess.check_call([venv_pip, 'install', 'python-tds=={}'.format(pytds_ver)])

    # install django-mssql
    #subprocess.check_call([venv_pip, 'install', 'git+https://bitbucket.org/Manfre/django-mssql.git#egg=django-mssql'])

    runtests_path = os.path.join(django_folder, 'tests', 'runtests.py')
    env = os.environ.copy()
    env['PYTHONPATH'] = ':'.join([django_folder, mssql_folder, 'tests', '.'])
    exclude_params = []  # ['--exclude-tag={}'.format(test) for test in exclude_tests]
    params = [venv_python, runtests_path, '--noinput', '--settings=test_mssql'] + exclude_params + tests
    subprocess.check_call(params, env=env)


if __name__ == '__main__':
    for django_ver in django_versions:
        for pytds_ver in pytds_versions:
            run_tests(django_ver, pytds_ver)
    print('PASS')
