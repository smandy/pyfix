
import yaml
f = open('tmp.yaml','r').read()
d = yaml.load( f )

print yaml.dump_all( [ { 'initiators' : d['initiators' ] },
                       { 'acceptors'  : d['acceptors'  ] } ] )

