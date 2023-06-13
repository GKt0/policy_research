from flask import Flask, render_template, request, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, validators, PasswordField, RadioField, DateTimeField, DateField, IntegerRangeField
import re
from datetime import datetime, date


#translation import, variables
import deepl

#Semantic search
import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

#ISO 639-1
source_langs = {
    "French" : "FR",
    "English" : "EN",
    "Bulgarian" : "BG",
    "Czech" : "CZ",
    "Danish" : "DA",
    "German" : "DE",
    "Greek" : "EL",
    "Spanish" : "ES",
    "Estonian" : "ET",
    "Finnish" : "FI",
    "Hungarian" : "HU",
    "Italian" : "IT",
    "Lithuanian" : "LT",
    "Latvian" : "LV",
    "Dutch" : "NL",
    "Polish" : "PL",
    "Portugese" : "PT",
    "Romanian" : "RO",
    "Slovak" : "SK",
    "Slovenian" : "SL",
    "Swedish" : "SV"
}
#ISO 639-1 and ISO 3166-1
target_langs= {
    "French" :"FR",
    "Belgium - fr":"FR",
    "Belgium - nl":"NL",
    "Belgium - de":"DE",
    "English (British)": "EN-GB",
    "English (American)" :"EN-US",
    "Bulgarian" : "BG",
    "Czech" : "CS",
    "Danish" : "DA",
    "German" : "DE",
    "Greek" : "EL",
    "Spanish" : "ES",
    "Estonian" : "ET",
    "Finnish" : "FI",
    "Hugarian" : "HU",
    "Italian" : "IT",
    "Lituanian" : "LT",
    "Latvian" : "LV",
    "Dutch" : "NL",
    "Polish" : "PL",
    "Portugese" : "PT-PT",
    "Slovak" : "SK",
    "Slovenian" : "SL",
    "Swedish" : "SV",
    "Romanian" : "RO"
}
#ACS query language
# https://azuresdkdocs.blob.core.windows.net/$web/python/azure-search-documents/11.3.0b6/azure.search.documents.models.html#azure.search.documents.models.QueryLanguage
query_langs={
    "FR" : "fr-fr",
    "PT-PT" : "pt-pt",
}


appInstance = Flask(__name__)
appInstance.config['SECRET_KEY'] = "khkjglulqusgdfmq891630piypy"


## -------- classes ----------------------------- ##
class LoginForm(FlaskForm):
    username = StringField(u'Username')
    password = PasswordField(u'Password')

class SearchForm(FlaskForm):
    query = StringField(u'Write your query')
    search_types = {"Semantic search" :"semantic", "using Lucene syntax":"full", "keywords based":"simple"}
    source_lan = SelectField(u'Source language', choices=[("EN", 'English (default)')])
    #target_langs = BooleanField(u'Translate in...', false_values=False)
    target_langs_options = target_langs
    starting_date = DateField(u'From')  # add help text with `description`
    end_date = DateField(u'to')  # add help text with `description`
    
    #Country = target_langs
    #country = SelectField(u'Country', choices=[('*', 'All'),('FR', 'France'), ('PT', 'Portugal')])
    
#class translation():
    
    
## -------- backend functions ------------------- ##
def clean(seq):
    return re.search(r'(?<=\-).*',seq).group(0)

def analyseQuery(seq):
    excluded = []
    included = []
    seqs = seq.split(",")
    for s in seqs:
        if s.startswith("-") or s.startswith(" -"):
            s = clean(s)
            print("excluded but cleaned ?: "+s)
            excluded.append(s)
        else:
            included.append(s)
    return [included, excluded]

def extractCountryCode(s):
    if len(s) == 2:
        return s
    pattern = re.compile(r'^[A-Z]{2}-([A-Z]{2})$')
    match = pattern.match(s)
    if match:
        return match.group(1)
    else:
        raise ValueError('Invalid format')
               
def translate(input, source, target):
    #language detection wasnt accurate enough to let the user write in any language
    #default source is 'EN', user has no choice atm.
    
    AUTH_KEY = "YOUR_DEEPL_KEY"
    translator = deepl.Translator(AUTH_KEY)
    translation = translator.translate_text(input, target_lang=target,source_lang=source)
    #translation = []
    # #include single or multiple targets translations
    # for code_lan in targets:
    #     if(type(input) == list):
    #         for seq in input:
    #             translation.append(translator.translate_text(seq, target_lang=code_lan, source_lang=source))
    #     else:
    #         translation.append(translator.translate_text(input, target_lang=code_lan, source_lang=source))
    
    # for t in translation:
    #     print(t.text)
    print("Translated to: "+ translation.text)
    return translation

def simpleQueryACS(input, target_lang, start_date, end_date):
    #find query_lang abrv based on target_lang
    try: 
        query_lang = query_langs[str(target_lang)]
    except KeyError:
        return ['0']
        
    #format country abrv for filter based on target_lang
    country = extractCountryCode(target_lang)
    filter_str = "country eq '"+country+"'"
    if(start_date and end_date):
        filter_str += "and journal_dateType le "+str(end_date)+"T00:00:00Z and journal_dateType ge "+str(start_date)+"T00:00:00Z"
    
    client = createSearchClient(country) # search client will depends on country (diff index for diff country)
    results = client.search(search_text = input, top=10, query_type='simple', query_language=query_lang, filter=filter_str)  
    return results
    
    #if(country == "PT"):
            
    
def semanticQueryACS(inputs, target_lang, start_date, end_date):
    #Documentation: https://azuresdkdocs.blob.core.windows.net/$web/python/azure-search-documents/11.3.0b6/azure.search.documents.aio.html
        
    results = []
    #find query_lang abrv based on target_lang
    try: 
        print(target_lang)
        query_lang = query_langs[str(target_lang)]
        print("In semanticQueryACS, query_lang: " + query_lang)
    except KeyError:
        return ['0']
        
    #format country abrv for filter based on target_lang
    country = extractCountryCode(target_lang)
    print("Country: "+ country)
    filter_str = "country eq '"+country+"'"
    if(start_date and end_date):
        filter_str += "and journal_dateType le "+str(end_date)+"T00:00:00Z and journal_dateType ge "+str(start_date)+"T00:00:00Z"
    
    client = createSearchClient(country)
    results = client.search(search_text = inputs, top=2, query_type="semantic", query_language=query_lang, semantic_configuration_name="semanticsearchconfig",highlight_fields="child_text,article_title", highlight_pre_tag="<mark>", highlight_post_tag="</mark>", filter=filter_str)
    #print("Results:")
    #print(results)
    return results

#Feature not implemented
def luceneQueryACS():
    return ""

def createSearchClient(country):
    # Mandatory variables
    service_name="pwc-leda"
    if(country =="FR"):
        index_name = "fr-origin-1m-filterable"
    else:
        #index_name = "pt-origin-filterable"
        index_name = "pt-origin"
    # Get the service endpoint and API key from the environment
    endpoint = "https://{}.search.windows.net/".format(service_name)
    #Only read key
    key = "YOUR_KEY"
    # Create a client
    credential = AzureKeyCredential(key)
    client = SearchClient(endpoint=endpoint,
                        index_name=index_name,
                        credential=credential)
    
    return client



## -------- routing ----------------------------- ##
@appInstance.route("/", methods=['GET','POST'])
def login():
    login_form = LoginForm()
    
    if login_form.validate_on_submit():
        
        print("submit has ben done")
        #retrieve inputs
        uName = login_form.username.data
        pW = login_form.password.data
        #check in DB...
        
        
        #if yes...
        #clean fields
        login_form.username.data = ""
        login_form.password.data= ""
        return redirect(url_for('form'))
        #else display notification

    
    return render_template('login.html', form=login_form)
    


@appInstance.route("/signUp")
def signUp():
    return render_template("signUp.html")

@appInstance.route("/form", methods=['GET','POST'])
def form():
    search_form = SearchForm()
    keyw_excluded_t = [] # is not displayed anymore, used to display lucene syntax query use cases
    keyw_included_t = [] # is not displayed anymore
    res = []
    #Check if the form has been submitted
    if search_form.validate_on_submit():
        #print(request.form.getlist('target_lan_selection'))    
        #Form values once submitted
        post_keywords = search_form.query.data
        post_source_lan = search_form.source_lan.data
        post_target_langs_selected = request.form.getlist('target_lan_selection')
        post_search_type = request.form.get('search_type_selected')
        post_starting_date = search_form.starting_date.data
        post_end_date = search_form.end_date.data
        print(post_starting_date)
        print(post_end_date)
        print(post_search_type)
        #analyseQuery: do analyse and transform the text input.
        # It returns a list of 2 list (words/seq to include, words/seq to exclude)
        #keywords = analyseQuery(post_keywords)
        keywords = post_keywords
        if keywords:
            print('keywords=%s' % keywords)
            #Lucene syntax
            # if(len(keywords[0])>=1):
            #     keyw_included_t = translate(keywords[0], post_source_lan, post_target_langs_selected)
            # if(len(keywords[1])>=1):
            #     #not taken into account for the query in ACS yet.
            #     keyw_excluded_t = translate(keywords[1], post_source_lan, post_target_langs_selected)
            #res = (queryACS(keyw_included_t, post_search_type))
               
            #keyw_included_t = ['taxe']
            #res = (queryACS(keyw_included_t, post_search_type))
            keywords_translated = []
            for l in post_target_langs_selected:
                keywords_translated.append(translate(keywords, post_source_lan, l))
            
            for idx in range(0,len(post_target_langs_selected)):
                if(post_search_type == 'simple'):
                    res.extend(list(simpleQueryACS(keywords_translated[idx], post_target_langs_selected[idx], post_starting_date, post_end_date)))
                    print("--------------------")
                    #print(res)
                #The part with semantic search is working correctly: dealing with several chosen sources. Copy that for 'full' and 'simple'
                elif(post_search_type == 'semantic'):
                    print(idx)
                    print(keywords_translated[idx])
                    res.extend(list(semanticQueryACS(keywords_translated[idx], post_target_langs_selected[idx], post_starting_date, post_end_date)))
                    #print("--------------------")
                    #print(res)
                    
                    
                # case, lucene syntax: post_search_type == 'full'):
                else:
                    res = luceneQueryACS()    
                try: 
                    if(res[0] == '0'):
                        errors=['The legal texts from the selected country are not available yet. We are working on it.']
                        return render_template('results.html',form=search_form, keywords = keywords_translated, excluded = keyw_excluded_t, res = res, errors=errors, search_type_select=post_search_type)
                except TypeError:                
                    return render_template('results.html',form=search_form, keywords = keywords_translated, excluded = keyw_excluded_t, res = res,  search_type_select=post_search_type)
                except IndexError:
                    return render_template('results.html',form=search_form, keywords = keywords_translated, excluded = keyw_excluded_t, res = res,  search_type_select=post_search_type)
                
            #final
            return render_template('results.html',form=search_form, keywords = keywords_translated, excluded = keyw_excluded_t, res = res,  search_type_select=post_search_type)
                
    else:
        #1st Loading on /form without having submit anything yet
        return render_template('filters.html', form=search_form)

#not used
@appInstance.route("/search")
def search(kit, ket):
    return render_template('search.html', keywords = kit, excluded = ket)

#not used   
@appInstance.route("/login")
def bease2():
    return render_template('login.html')
    

appInstance.run()