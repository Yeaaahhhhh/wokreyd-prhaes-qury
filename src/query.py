import math
import sys
import string
import json
import math
import re
from collections import defaultdict
from indexCreation import getDocContent, getAllDf, atf, probIdf

def punctCheck(Q):
    '''
    Function: This function is a total check of parenthesis and "logic operators",i.e. (,),AND,OR,NOT
              If both of them return True, then it passes the basic check of operators
              It will change the Q, the argument, in str type, to a list, splited by spaces.
    Argument:Argument Q is a input query, in the type of string, for example: 'book:Harry AND line:Potter'
    Return: return a boolean value True or False
    '''
    syms = "!~`@#$%^&*_+=-|\;<,.>?/"+'{'+'}'
    for i in Q:
        if i in syms:
            return False
    return True

def colonsEven(Q):
    '''
    Function: This function check whether the colons are paired
    It will be used in phrase query and mixed query check

    Argument: Q, the input query

    Return: boolean value
    '''
    # Count the number of colons in the sentence
    num_colons = Q.count(':')
    # Check if the number of colons is even
    if num_colons % 2 == 0:
        return True
    return False

def getQuery():
    '''
    Function: This function get the user second input comand line argument, which is a query in '...abc:de AND asdf:fsa' form
              Then it check whether the input query are properly formed using above functions punctCheck() and checkLogiExist()
              If something error occurred, it should print out a stderr message.

    Argument: None
    Return: a query in str type, and a value 'k' in int type.

    '''
    try:
        numCommandArg = 4
        if len(sys.argv) != numCommandArg:
            sys.stderr.write('Give more or less command line arguments, make sure the amount of arguments is correct\n')
            sys.exit()
        kLines = int(sys.argv[2])  # the second arg is the number of lines gonna returned
        query = str(sys.argv[3])   # the third arg is the query
        if punctCheck(query) == False:
            sys.stderr.write(
                'query contains invalid symbols, please input a valid query again\n')
            sys.exit()
        if colonsEven(query) == False:
            sys.stderr.write(
                'check phrase queries colons\n, please input a valid query again\n')
            sys.exit()
    except Exception:
        sys.stderr.write('User input argument error\n' +
                         'or the value of input k is not an integer\n')
        sys.exit()
    return query, kLines

def getAll():
    '''
    Function: this function will get all  doc_id from the tsv file, the indexCreation.py will insert a line at the very beginning to show all doc_ids,
              The function will be used later for 'NOT book:Lorax', we will use set operation to find its complement by implementing U set

    Return: a set contains all doc_id in that appear in the zone.tsv file, first line index.
    '''
    with open(str(sys.argv[1])+'invertedIndex.tsv', encoding='utf-8') as file:
        ro = 1
        for line in file:
            row1 = line.strip().split('\t')
            ro += 1
            if ro == 3:
                rowList = ast.literal_eval(row1[1])
                postings = set(rowList)
                return postings


    '''
    This function parse the user query, find all phrase query and keyword query, return them separately.

    '''
def splitKeyAndPhrase(query):
    '''
    This function parse the query user input, the query can be very disorganized, the function return a 
    normalized query, and identify them to keyword or phrase, for fastCosineScore usage.

    Arg: query, user input, disorganized

    return: two list, phrase and keyword list.
    '''
    phrase_list = re.findall(r':\s*([^:]+?)\s*:', query)
    keyword_list = re.findall(r'\b([^:\s]+)\b', query)
    for phrase in phrase_list:
        keyword_list = [word for word in keyword_list if phrase.find(word) == -1]
    phrase_list = [phrase.strip() for phrase in phrase_list]
    return phrase_list, keyword_list



def createPoolDoc(Q):
    """
    Returns a list of dictionaries containing documents from a JSON file that match a user query.
    
    Args:
    - json_file_path (str): Path to JSON file containing documents.
    - Q (str): Query phrase to search for in document contents.
    
    Returns:
    - A list of dictionaries containing matching documents.
    """
    phraseList = splitKeyAndPhrase(Q)[0]                  
    keywordList = splitKeyAndPhrase(Q)[1]
    poolIndexList = []                                    
    phraseList.extend(keywordList)

    pool = []                                              
    with open(sys.argv[1]+"path.txt","r") as output_file:
        json_file = output_file.read()

    with open(json_file, 'r') as f:
        documents = json.load(f)
    Docs = []               
    for d in documents:
        Docs.append(getDocContent(d)) 
    for p in phraseList:
        for doc in Docs:
            if doc['doc_id'] in poolIndexList:
                continue
            else:
                if p.lower() in doc['content'].lower():
                    pool.append(doc)
                    poolIndexList.append(doc['doc_id'])
    return pool

def fastCosineScore(q):
    '''
    This function takes the algorithm on textbook 7.1 and follow the scheme apc.btn for score calculation
    We use the created pool here to improve the efficiency of calculating the score.
    The term weight are set to 1 based on the textbook.

    Arg: query, the organized one

    return: similarity score
    '''
    skip = 0
    with open(sys.argv[1]+"path.txt","r") as output_file:
        json_file = output_file.read()
    with open(json_file, 'r') as f:
        documents = json.load(f)

    docIndexList = []
    with open(sys.argv[1]+'documentIndex.tsv','r',encoding = 'utf-8') as docFile:
        for line in docFile:
            if skip == 0:
                skip += 1
                continue
            docIndexList.append(line.strip().split('\t'))   #first doc_id, second is vector norm
    N = len(documents)
    sumWeight = 0
    df = getAllDf(sys.argv[1])
    df = defaultdict(lambda:0,df)
    pool = createPoolDoc(q)

    phraseList,keywordList = splitKeyAndPhrase(q)
    term_list = keywordList
    unique_term_list = list(set(term_list))  #every query term (can be keyword or can be phrase)
    for phrase in phraseList:
        words = phrase.split()
        term_list.append(phrase)
    
    # calculate Wt,q = tf*idf
    # tf = 0/1, idf = log(N/df)
    storeTermList = []  # store all term query -->doc1, next loop, query -->doc2,
    scoreList = []
    scoreDict = {}
    for p in pool:

        storeTermList = unique_term_list
        contentList = p['content'].split()
        storeTermList.extend(contentList)
        
        for di in docIndexList:
            if di[0] == p['doc_id']:
                dNorm = float(di[1])
                break
        for term in storeTermList:
            tf_idf_p = 0
            df[term] = int(df[term])
            if df[term] == 0:
                weight_tq = 0
            else:
                weight_tq = 1 * math.log(N/df[term])
                tf_idf_p = max(0,math.log((N-df[term])/df[term]))
            if weight_tq != 0:
                weight_tq = 1
            tf_idf_a = atf(term,p['content'])

            doctermWeight = tf_idf_a * tf_idf_p
            sumWeight += doctermWeight*weight_tq
        finalScore = sumWeight/dNorm
        scoreDict = {}
        scoreDict['doc_id'] = p['doc_id']
        scoreDict['score'] = format(finalScore,'.2f')
        scoreList.append(scoreDict)
    length_nonZero = 0
    for i in scoreList:
        if i['score'] != 0:
            length_nonZero += 1
    return len(pool), length_nonZero, scoreList

def main():
    path = sys.argv[1]          # It is the path where
    userQuery = getQuery()[0]   # 'Lorax The hello you'
    numLines = getQuery()[1]    # 17
    numDocForQ, numDocWithScore, scoreList = fastCosineScore(userQuery)
    sys.stdout.write(str(numDocForQ))  #it is the length of pool (dictionary) which contains matched docs
    print('')
    sys.stdout.write(str(numDocWithScore)) #get the number of docs with non-zero score
    print('')
    index = 0
    sortedScoreList = sorted(scoreList, key=lambda x: float(x['score']), reverse=True)
    while numLines != 0 and numDocWithScore != 0:
        numLines -= 1
        numDocWithScore -= 1
        sys.stdout.write(sortedScoreList[index]['doc_id'] + '\t' + sortedScoreList[index]['score'])
        index += 1
        print('')

if __name__ == "__main__":
    main()
    

