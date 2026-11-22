"""Explicit private fixed rows: restore field names, never semantic values."""
import copy
import json
from . import named_reference_wire as named

SCHEMA = VERSION = 'cocolon.cmee.fixed_rows_comparison.v1'

def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False)

FIELDS = {
    'root':['v','a','q','c'],
    'q':['id','s','f','t'],
    'c':['claims','conflicts','core','question','relations','schema','unknowns','updates','prose'],
    'claim':['time','cid','ev','kind','mode','polarity','pred','qual','subject','text'],
    'time':['at_source','ev','expr','kind'],
    'mode':['ev','value'],
    'polarity':['ev','scope','value'],
    'pred':['args','surface'],
    'subject':['bind','ev','entity'],
    'relation':['ev','from','polarity','qual','rid','scope','to','type'],
    'update':['ev','op','prior','replace','target_kind','target','$id'],
    'prose':['binds','observation','reception','update_note'],
    'bind':['cr','rr','section'],
}

def need(ok,reason):
    if not ok: raise ValueError(reason)


def obj(kind,value):
    keys=FIELDS[kind]
    need(type(value) is list,'row_not_list:'+kind)
    if kind=='bind' and len(value)==4: keys=keys+['ur']
    need(len(value)==len(keys),'row_arity:'+kind)
    return dict(zip(keys,copy.deepcopy(value)))


def strings(v):
    return type(v) is list and all(type(x) is str for x in v)


def decode_named(value):
    need(type(value) is list and len(value)==5 and value[0]==VERSION,'fixed_rows_version_or_root')
    r=obj('root',value[1:]); need(type(r['v']) is str,'v_not_string')
    need(type(r['a']) is list,'aliases_not_rows')
    aliases={}
    for pair in r['a']:
        need(type(pair) is list and len(pair)==2 and all(type(x) is str for x in pair),'alias_shape')
        need(pair[0] not in aliases,'duplicate_alias')
        aliases[pair[0]]=pair[1]
    r['a']=aliases
    need(type(r['q']) is list,'quotes_not_list')
    r['q']=[obj('q',q) for q in r['q']]
    need(all(all(type(v) is str for v in q.values()) for q in r['q']),'quote_cell_type')
    c=obj('c',r['c']); r['c']=c
    need(all(type(c[k]) is list for k in ['claims','conflicts','relations','unknowns','updates']),'candidate_list_type')
    need(type(c['core']) is str and type(c['schema']) is str,'candidate_string_type')
    claims=[]
    for raw in c['claims']:
        claim=obj('claim',raw)
        for k in ['time','mode','polarity','pred','subject']: claim[k]=obj(k,claim[k])
        need(all(type(claim[k]) is str for k in ['cid','kind','text']),'claim_string_type')
        need(strings(claim['ev']) and type(claim['qual']) is list,'claim_list_type')
        need(type(claim['time']['at_source']) is str and strings(claim['time']['ev']) and
             (claim['time']['expr'] is None or type(claim['time']['expr']) is str) and type(claim['time']['kind']) is str,'time_cell_type')
        need(strings(claim['mode']['ev']) and type(claim['mode']['value']) is str,'mode_cell_type')
        need(strings(claim['polarity']['ev']) and strings(claim['polarity']['scope']) and type(claim['polarity']['value']) is str,'polarity_cell_type')
        need(type(claim['pred']['args']) is list and type(claim['pred']['surface']) is str,'predicate_cell_type')
        need(type(claim['subject']['bind']) is str and strings(claim['subject']['ev']),'subject_cell_type')
        claims.append(claim)
    c['claims']=claims
    c['relations']=[obj('relation',v) for v in c['relations']]
    for relation in c['relations']:
        need(strings(relation['ev']) and strings(relation['scope']) and type(relation['qual']) is list,'relation_list_type')
        need(all(type(relation[k]) is str for k in ['from','polarity','rid','to','type']),'relation_string_type')
    c['updates']=[obj('update',v) for v in c['updates']]
    for update in c['updates']:
        need(strings(update['ev']) and strings(update['replace']),'update_list_type')
        need(all(type(update[k]) is str for k in ['op','prior','target_kind','target','$id']),'update_string_type')
    prose=obj('prose',c['prose']); c['prose']=prose
    need(type(prose['binds']) is list and all(type(prose[k]) is str for k in ['observation','reception','update_note']),'prose_cell_type')
    prose['binds']=[obj('bind',v) for v in prose['binds']]
    for bind in prose['binds']:
        need(strings(bind['cr']) and strings(bind['rr']) and type(bind['section']) is str,'bind_cell_type')
        if 'ur' in bind: need(strings(bind['ur']),'update_binding_type')
    compact(r)
    return r



def decode(value):
    return named.decode(decode_named(value))


def accepts_material(material):
    """Bound syntax admission to the written BOOK/SHOP answer source pair.

    This grants no semantic adoption. The existing independent source reader
    validates the entire answer, prior, pending question and meaning again.
    """
    if (material.get('execution_mode') != 'OFFLINE_PREPARATION'
            or material.get('adoption_state') != 'NOT_ADOPTED'
            or material.get('core') != 'emlis' or material.get('tier') != 'free'
            or material.get('task') != 'EMLIS_ANSWER_MATERIAL'):
        return False
    sources = material.get('sources', [])
    if len(sources) != 2 or [s.get('role') for s in sources] != ['ORIGINAL_INPUT', 'SUPPLEMENTAL_ANSWER']:
        return False
    fields = sources[0].get('text_fields', {})
    originals = {
        ('借りていた本を返すのが遅れて、友人に謝った。', '大丈夫って言ってくれたけど、まだちょっと気になる。'),
        ('昔からの友人が店を開いたと知って、お祝いのメッセージを送った。', 'うれしかったけど、少し置いていかれた気がした。'),
    }
    return (fields.get('memo_action'), fields.get('memo')) in originals
