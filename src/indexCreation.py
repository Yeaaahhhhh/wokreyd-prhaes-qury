
import json
import sys
import csv
import unicodedata
import string
import math
from collections import defaultdict, Counter

def checkCommendLineArgs():
  """
    Check the command line arguments are correct
    Args:
      None
    Return:
      None
  """
  if len(sys.argv) != 3:
    sys.stderr.write("Give more or less command line arguments\n")
    sys.exit()

def checkId(data):
  '''
  Function: 
    Check each document has a doc_id, check no two document have the same id, check doc_id must be an integer
  Arguments: 
    data: json object
  Return: 
    Boolean: return true if all the checks pass, otherwise, print stderr message and exit the program
  '''
  key_list = []
  for doc in data:
    if "doc_id" not in doc.keys():
      sys.stderr.write("Document does not have a doc_id, try again\n")
      sys.exit()
    else:
      try:
        doc_id = doc['doc_id']
        doc_id = int(doc_id)
      except:
        sys.stderr.write("not a valid id,try again\n")
        sys.exit()
      if doc_id not in key_list:
        key_list.append(int(doc['doc_id']))
      else:
        sys.stderr.write("repeated doc_id\n")
        sys.exit()
  return True

def checkZone(data):
  ''' 
  Function: 
    Check each zone name in each document must be a single token_df_postings_dict, 
    check each document must have at least one zone ,check each zone has some text
  Arguments:
    data: json object
  Return:
    Boolean: return true if all the checks pass, otherwise, print to stderr and exit the program
  '''
  punctuations = string.punctuation
  for doc in data:
    keys = doc.keys()
    if len(keys) <= 1:
      sys.stderr.write("At least one document doesn't have zones!\n")
      sys.exit()
    for zone in keys:
      if zone != 'doc_id':
        if doc[zone] == "":
          sys.stderr.write("no text")
          sys.exit()
        token_list = zone.split(" ")
        if len(token_list) > 1:
          sys.stderr.write("Zone name must be a single token! Cannot have spaces.\n")
          sys.exit()
        for char in zone:
          if char in punctuations:
            sys.stderr.write("Zone name must be a single token! Cannot have punctuations.\n")
            sys.exit()
  return True

def checkAll(data):
  '''
  Function: 
    Combine function checkZone and checkId 
  Arguments:
    data: json object
  Return:
    Boolean: return true if both functions return true
  '''
  checkId(data) & checkZone(data)

def removeAccentMarks(input_list):
  output_list = []
  for input_str in input_list:
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    output_list.append(u"".join([c for c in nfkd_form if not unicodedata.combining(c)])) 
  return output_list

def wordListCaseSensitive(word_list):
  '''
  Function: 
    Convert every word in a list to lowercase
  Arguments:
    word_List: list
  Return: 
    result_list: list 
  '''
  result_list = []
  for word in word_list:
    result_list.append(word.lower())
  return result_list

def createToken(zone,data):
  '''
  Function: 
    Create tokens for each zone, store tokens and their corrsponding postings to a dictionary,
    and sort them into a list by term name.
  Arguments:
    zone: name of the zone, type: str
    data: json object
  Return:
    merged_list: a list of tuples, where the first element in the tuple is the term name, 
    and the secound element is the postings list containing doc_ids
  '''
  term_list = []
  for doc in data:
    if zone not in doc.keys():
      continue
    terms = doc[zone].split(" ")
    terms = wordListCaseSensitive(terms)
    terms = removePunctuation(terms)
    terms = removeAccentMarks(terms)
    terms = list(set(terms))
    
    terms.sort()
    for term in terms:
      if term == "":
        continue
      temp_dict = {}
      temp_dict[term] = doc['doc_id']
      term_list.append(temp_dict)
  merged_dict = {}
  for dic in term_list:
    for k,v in dic.items():
      if k not in merged_dict:
        merged_dict[k] = [v]
      else:
        merged_dict[k].append(v)
  for i in merged_dict:
    merged_dict[i].sort()
  merged_list = sorted(merged_dict.items())
  merged_list
  return merged_list

def removePunctuation(input_list):
  '''
  Function: 
    Remove punctuations in every word in a list
  Arguments: 
    input_list: a list of strings
  Return:
    output_list: a list of strings with no punctuations
  '''
  punctuations = string.punctuation
  translator = str.maketrans("", "", punctuations)
  output_list = [s.translate(translator) for s in input_list]
  return output_list

def createTokenDfPostings(zone,data):
  '''
  Function:
    Create a dictionary that contains tokens, document frequency, and postings,
    with token as the key, and a tuple of df and postings as the value.
  Arguments:
    zone: name of the zone, type: str
    data: json object
  Return:
    token_df_postings_dict,   {you: (4,[1,2,3,6])}
      type - dictionary
      key - token
      value - tuple of df and postings list
  '''
  token_df_postings_dict = {}
  token_dict = createToken(zone, data)
  for i in token_dict:
    old_v = i[1]
    freq = len(old_v)
    token_df_postings_dict[i[0]] = (old_v,freq)
  return token_df_postings_dict

def writeToTSV(fileName,token_df_postings_dict, data):
  '''
  Function: 
    write data into the tsv file. Here, data is three columns, with
      first column: token,
      second column: document frequency,
      third column: postings
  Arguments:
    filename: the name of the file to write to
    token_df_postings_dict: a dictionary that contains token, df, postings
    data: json object
  Return:
    no return
  '''
  # sys.argv[2]: path to the directory where the index files will be stored
  with open( fileName, 'wt', encoding='utf-8') as out_file:
    tsv_writer = csv.writer(out_file, delimiter='\t')
    tsv_writer.writerow(['token','DF','postings'])
    for token, value in token_df_postings_dict.items():
      df = value[1]
      docIDs = value[0]
      tsv_writer.writerow([token,df,'[' + ','.join(docIDs) + ']'])
    # tsv_writer.writerow([sys.argv[1]])

def getData():
  '''
  Function:
    Load json data from a json file.
  Arguments:
    None
  Return:
    data: a json object
  '''
  try:
    with open(sys.argv[1], "r") as f:
      data = json.load(f)
  except Exception:
    sys.stderr.write("inappropriate arguments, try again\n")
    sys.exit()
  return data

def getAllZones(data):
  '''
  Function:
    get all the zones in the json object
  Arguments:
    data: json object
  Return:
    zones: a list of all the zones in the data
  '''
  zones = []
  for doc in data:
    keys = doc.keys()
    for zone in keys:
      if zone != 'doc_id':
        zones.append(zone)
  zones = list(set(zones))
  return zones

def createIndex(data):
  '''
  Function:
    create the index files by calling writeToTSV function
  Arguments:
    None
  Return:
    None
  '''
  checkCommendLineArgs()
  checkAll(data)
  zones = getAllZones(data)
  total = {}
  for zone in zones: 
    token_df_postings_dict = createTokenDfPostings(zone,data)
    for token in token_df_postings_dict:
      if token not in total.keys():
        total[token] = token_df_postings_dict[token]
      else:
        temp = total[token][0]
        temp.extend(token_df_postings_dict[token][0])
        temp = list(set(temp))
        temp.sort()
        total[token] = (temp, len(temp))
  sorted_total = dict(sorted(total.items()))
  try:
    writeToTSV(sys.argv[2] + '/invertedIndex.tsv',sorted_total,data)
  except Exception as e:
    raise Exception(e)
    sys.stderr.write('storage path error or lack of command line argument\n')
    sys.exit()

def atf(term, document):
    '''
    This function is the calculation of term frequency using augmented scheme a

    '''
    tf = document.count(term)

    # Calculate the maximum raw term frequency
    max_tf = max(document.count(t) for t in set(document))

    # Calculate the augmented term frequency
    atf = 0.5 + 0.5 * (tf / max_tf)

    return atf

def probIdf(collection_len, df):
    '''
    This function is the calculation of document frequency using scheme p, prob idf

    Parameter:
        collection: the json file contains all documents
        df: document frequency of that term calculated in the indexCreation step

    Return: the calculation of logrithmic value
    '''
    df = int(df)
    result = max(0, math.log((collection_len-df)/df))
    return result

def getAllDf(path):
  """
    Get all the document frequency for each term, and store them in a dictionary
    Args:
    path (str): the path to the invertedIndex.tsv

    Return:
    a dictionary with key=term_name, and value=df
  """
  df_dict = {}
  try:
    with open(str(path) + "invertedIndex.tsv", encoding='utf-8') as files:
      for line in files:
        columns = line.strip().split("\t")
        if columns[0] == "token" or columns[0]=='':
          continue
        df_dict[columns[0]] = columns[1]
  except Exception as e:
    raise Exception(e)
  return df_dict

def getDocContent(doc):
  """
    Get contents from all zones in a document.

    Args:
    doc (dict): a dictionary, the format is the same as dictionary in data/dr_seuss_lines.json file

    Returns:
    docDict (dict): a dictionary with two key-value pair, "doc_id" and "content" as keys
  """

  content =''
  docDict = {}
  for k,v in doc.items():
    if k != 'doc_id':
      content += v
      content += ' '
  docDict['doc_id'] = doc['doc_id'] 
  docDict['content'] = content.strip()
  return docDict

def calcualteDocLen(jsonFile,tsvFile):
  """
    Calculates the score of each document in a JSON file containing
    thousands of documents in dictionary format, and writes the results
    to a TSV file.
    
    Args:
    jsonFile (str): The path to the input JSON file.
    tsvFile (str): The path to the output TSV file.
    
    Returns:
    None.
  """
  with open(jsonFile, 'r') as f:
    documents = json.load(f)

    # Calculate the document frequency of each term
    df = getAllDf(sys.argv[2])
    df = defaultdict(lambda: 0, df)
    
    # Calculate the norms and write them to the output TSV file
    with open(tsvFile, 'wt', encoding='utf-8') as out_file:
        writer = csv.writer(out_file, delimiter='\t')
        N = len(documents)
        writer.writerow(['doc_id','length'])
        for doc in documents:
            doc_id = doc['doc_id']
            words = getDocContent(doc)['content']
            punctuations = string.punctuation
            translator = str.maketrans("", "", punctuations)
            words = words.translate(translator)
            words = words.split()
            words = removeAccentMarks(words)
            
            tf = Counter(words)
            max_tf = max(tf.values())
            leng = 0
            for word, freq in tf.items():
              df[word] = int(df[word])
              tf = 0.5 + 0.5 * freq / max_tf
              if df[word] == 0 or (N-df[word]) == 0:
                p_idf = 0
              else:
                p_idf = max(0,math.log((N-df[word])/df[word]))
              tf_idf = tf * p_idf
              leng += tf_idf ** 2
            leng = math.sqrt(leng)
            leng = format(leng,'.2f')
            writer.writerow([doc_id, leng])

if __name__ == "__main__":
  data = getData()

  with open(sys.argv[2] + "path.txt","w") as out_file:
    out_file.write(sys.argv[1])

  createIndex(data)
  calcualteDocLen(sys.argv[1],sys.argv[2] + 'documentIndex.tsv')
  