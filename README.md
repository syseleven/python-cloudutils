python-cloudutils
=========

This repos contains several useful library to talk to OpenStack APIs and has some wrapper tools for it.



scloud
-----------

scloud is a wrapper that deletes existing stacks and re-creates them according to your config files and command line parameters.


Installation
-------------
```
virtualenv ~/syseleven-cloudutils-venv # optional
. ~/syseleven-cloudutils-venv/bin/activate # optional

# apt-get install python-dev # needed
pip install -e git+git@github.com:syseleven/python-cloudutils.git#egg=syseleven.cloudutils

```

Usage
--------------

You can pass as many config files as you want. One common concept would be to have at least two configuration files

 1. global config file
 2. per stack config file

Those contain a _DEFAULT_ section for scloud configuration and a _heat_params_ section for all parameters needing for creating the heat stack (i.e. the same as ```heat stack-create <name> -P key1=value -P key2=value```)
The _heatparamsfromfiles_ key in the _DEFAULT_ section is special. This parameter specifies a list of heat_params key that will be treated as files and their content will be replaced by the actual file content.
You may specifiy all heat_params with the command line option -P (multiple invocations possible). All given -P key=value pairs will overwrite the values from the config.



#### global config file ####
If you want to maintain a global config file you always have to pass it via --config-file to scloud.
If the global config file ~/scloud.conf is specified as first --config-file argument it will be parsed the beginning, so it may contain values that will be overwritten by the per-stack config file or by command line parameters.


```
[DEFAULT]
stackname=overwriteme
heattemplatebasepath=~/git/openstack-heattemplates/
[heat_params]
deploy_key=/Users/myuser/.ssh/openstack_deploykey
key_name=mykeyname
```


#### per stack config file ####
A per stack config file can be given as additional --config-file parameter to scloud. 

```
[DEFAULT]
stackname=mystack
# heattemplate may be a full path or relative path to heattemplatebasepath
heattemplate='dev-cloud.yaml'
heatparamsfromfiles=repos_yaml, deploy_key

[heat_params]
config_branch=master
scripts_branch=master
puppet_branch=master
public_net_id=aaaa-bbbb-ccc-ddd
repos_yaml=""
```

#### command line usage examples ####

* ```scloud --config-file ~/.scloud.conf --config-file mycloud.conf```
* ```scloud --config-file ~/.scloud.conf --config-file mycloud.conf -P key_name=myotherkey -P config_branch=myotherbranch```

Setting an alias to ```alias scloud="scloud --config-file ~/.scloud.conf --config-file "```should smoothen things up.
So you can just use ```scloud mycloud.conf```

listhosts
-----------

This tool lists all VMs with the information on which compute node they run. It requires admin privileges and lists all VMs from all tenants by default. It's not configureable yet.

```
$ listhosts
7dc32de0-e1b2-4c9b-8b6e-1e9e21eddf2d (hadoop-spark3) cloud18
d8b0d799-88d0-4e43-928b-8036752ea84d (hadoop-cassandra1) cloud19
7ef7b2c9-4c74-4393-b76d-54b4da54f6bf (hadoop-hdfs1) cloud18
a07c90ec-5f1f-43ee-90d6-4ebf03995c57 (hadoop-hdfs3) cloud19
[...]
```

Development
--------------
```
git clone git@github.com:syseleven/python-cloudutils.git
cd python-syseleven-cloudutils
# git checkout $branch
. /path/to/venv/bin/activate
python setup.py develop
```

Commands like scloud will then be linked to the git repo in the venv.

