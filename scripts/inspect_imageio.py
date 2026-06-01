import imageio
import importlib.metadata, site, os
print('imageio file:', getattr(imageio, '__file__', None))
try:
    dist=importlib.metadata.distribution('imageio')
    print('distribution:', dist.metadata['Name'], 'version', dist.version)
    print('dist files:', list(dist.files)[:10])
except Exception as e:
    print('dist error:', repr(e))
print('site-packages:', site.getsitepackages())
print('site-user:', site.getusersitepackages())
# Find imageio package path
import pkgutil
print('find_spec:', imageio.__package__)
print('basedir:', os.path.dirname(imageio.__file__))
