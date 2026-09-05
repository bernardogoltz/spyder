# Empacotamento de um plugin externo

## pyproject.toml mínimo

```toml
[build-system]
requires = ["setuptools>=64"]
build-backend = "setuptools.build_meta"

[project]
name = "spyder-meuplugin"
version = "0.1.0"
description = "Customizações pessoais do Spyder"
requires-python = ">=3.8"
dependencies = []            # NÃO liste spyder aqui; veja abaixo

[project.entry-points."spyder.plugins"]
meuplugin = "spyder_meuplugin.plugin:MeuPlugin"

[tool.setuptools.packages.find]
include = ["spyder_meuplugin*"]
```

Se preferir `setup.py` (é o que o próprio Spyder usa):

```python
setup(
    name='spyder-meuplugin',
    version='0.1.0',
    packages=find_packages(),
    entry_points={
        'spyder.plugins': [
            'meuplugin = spyder_meuplugin.plugin:MeuPlugin',
        ],
    },
)
```

## Por que não declarar `spyder` em `dependencies`

Você vai instalar o plugin no mesmo ambiente onde o Spyder já está. Declarar
`spyder>=5.5` como dependência faz o pip querer resolver/reinstalar o Spyder —
e num ambiente conda ou numa instalação de source (`pip install -e .` do fork)
isso costuma quebrar tudo. Prefira validar a versão em runtime:

```python
@staticmethod
def check_compatibility():
    from spyder import version_info
    if version_info[0] != 5:
        return False, _('Este plugin só funciona no Spyder 5.')
    return True, ''
```

## Instalar em dev

No ambiente do Spyder (o mesmo em que `python bootstrap.py` roda):

```powershell
pip install -e .
```

Editou o plugin? **Reinicie o Spyder.** Não há hot reload; os plugins são
instanciados uma vez no boot.

## Assets (ícones, imagens)

Se o plugin traz imagens próprias, aponte `IMG_PATH` na classe do plugin
(caminho relativo ao pacote) e inclua os arquivos no wheel:

```toml
[tool.setuptools.package-data]
spyder_meuplugin = ["images/*.svg", "images/*.png"]
```

## Traduções

`from spyder.api.translations import _` usa o catálogo do **Spyder**. Para
strings próprias traduzidas, crie seu domínio com
`spyder.config.base.get_translation('spyder_meuplugin')`. Para uso pessoal,
não vale a pena — deixe as strings no idioma que você usa.

## Estrutura de referência real

O melhor exemplo público é o `spyder-notebook` / `spyder-terminal` (repos da
organização spyder-ide). Dentro deste repo, o análogo mais próximo de um plugin
externo bem estruturado é `spyder/plugins/pylint/` — mesma anatomia, só que
registrado como interno.
