All your code should go here and nowhere else.

# libraries
   All moudule used are standard.
# run program
There are two programs that gonna use, one is indexCreation.py, another is query.py. The lines below show how to use them.

  1. create index files
    Example run program: 
      - python src/indexCreation.py data/dr_seuss_line.json ./
      - python src/indexCreation.py data/dr_seuss_line.json ./data/
      (**the index folder name had to include a '/' at the end**)
  2. querys
    Example run program:
      - python src/query.py ./ 5 'like you'
      **Note: As long as the query part contains spaces, it must have quotes to include it: 'good morning hello :you little coconut:'**

# Algorithms and Data Structure used
  - Index Creation
    Similar as Homework 1 Index Creation step, the difference is we don't need to consider the zone name and generate each zone name file at this time. We ignore the zones but only get those terms (getDocContent() function) of each zone, we add all those terms into one file called 'invertedIndex.tsv', since we only return the doc_id of matched docs with high scores (not zones).

    The second index file is documentIndex.tsv, it contains two coloumns, the first is the doc_id, the second is the vector length of the document (not the length of the document as a string). We first normalize the document terms such as remove accent, punctuations and so on, and same as IndexCreation, we ignore the zone names. And use 'apc' scheme (augmented tf, prob-idf, cosine normalization) to find out the weight, then sum them up and take square root of it. Then we can get the weight of wf_(t,d), and the vector length of document, add all of them into documentIndex.tsv file.



  - Query 

    ****As long as there are some characters in the term, for example, the word 'to' is in word 'tomorrow', then the doc_id of both terms will be returned ****
    The main algorithm is based in textbook 7.1 algorithm, the fastCosineScore, 

    First generate a documentIndex.tsv file which contains the vector norm of each document, then calculate the weight and query respectively, 
        Calculate the norm of 'di' which is the tf-idf weight based on the scheme apc, augmented tf, prob-idf, then square each of it, then sum them up, finally get the square root of the sum, which is the norm of the document.
    As specified in textbook algorithm 7.1, the w_tq is calculated as 1 if it is non-zero, so basically the product (score) of w_tq and w_td is w_td itself, finally divide the score by document norm(matched from documentIndex.tsv), return top K documents as needed.

    **For any document d, the cosine similarity ~V(q) · ~v(d) is the weighted sum,over all terms in the query q, of the weights of those terms in d. This in turn can be computed by a postings intersection exactly as in the algorithm of Figure 6.14, with line 8 altered since we take wt,q to be 1 so that the multiply-add in that step becomes just an addition.**------textbook 7.1 Algorithm


# Assumptions and Errors detected
  
  - Index Creation
    All the checks are done in functions checkId(data) and checkZone(data)
    - **the index folder name had to include a '/' at the end**

    - Each document must have one required field called doc_id
      print to stderr and exit the program if any document does not have a filed called doc_id

    - Each doc_id must be an integer
      print to stderr and exit the program if any doc_id is not an integer

    - No two documents have the same id
      print to stderr and exit the program if there are two documents have the same id

    - each document has at least one zone with some text associated with it
      print to stderr and exit the program if any document has only doc_id, and no text in a zone

    - each zone name must be a single token(no space, no punctuations)
      print to stderr and exit the program if any zone name is not a single token

    - Check that the number of command line arguments are correct, that is the index creation should have exactly three (length)
    
    - When every document does not contain every zone (indexCreation.py line 127, if zone not in doc.keys(), just skip it)

  - Query Program
   ************ -------------> Assumption: The query should be input by a English Keyboard!


    1. If the query only contains 'python query.py' without command line arguments or with only one command line argument, or the command line arguments not properly written, print to stderr and exit the program.

    2. If the user query contains !~`@#$%^&*_+=-{}|\;<,.>?/ symbols, print to stderr and exit the program as symbols error since the indexCreation program removes all those punctuations.
    
    3. based on the input value, we can figure out what type of the query it is.
    If does not contain colons(:), then it is a keyword query
    If contains ':', then it can be mixed or phrase query
        --If it is a phrase query
            -assumption: 
                1. it can have 2, 3, 4, 5 words......
                2. They must be delimited by two colons (error colon check, for example:  ':hello you'   need one more colon)
                3. If in form of ':hello you:hi you:', we handle this as an error, request a new input as ':hello you hi you:'
                4. If in form of ':hello you: hi :yes no', it is another error, lack of colons
                5. The phrase must not be an empty string
        --If it is a mixed query
            -assumption:
                1. The number of colons must be even(2,4,6,8,10...colons) so that the algorithm can find out which are keyword parts and which are phrase parts
                2. no punctuation in the query except colons
                3. The phrase part must not be an empty string
    4. Extension of #3, that is colons must be paired in a query, that is must be a even number, if odd, raise error, quit the sys and request a new input.

    5. Check that the number of command line arguments are correct, that is the index creation should have exactly four arguments (length)

    6. Use re moudule to handle the extra spaces problem, for example, 'you    :like   :' will be turned into 'you :like:' and 'like' will be added to phraseList and 'you' will be added to keywordList.

# References: 
    - https://docs.python.org/3/library/re.html
    - https://realpython.com/python-defaultdict/
    


# index creation Scheme
- apc.btn
  - document: tf(t,d), df(t), w
  - query: (boolean 1/0) ,df, 1

  | tf | tf-weight           | idf                   | weight = tf*idf  | normalization | normalized weight|
  |------------|------|------------|------|------------|------|
  | (0.5+0.5tf)/max(tf) | max{0,log((N-df)/df)} |                  | cosine norm.  | weight*normalization|------|
  | (0/1)               | log(N/df)             |                  |  1 |------------|------|
  

tf-weight, and idf -> weight
normalization, weight -> normalized weight
sum up all the normalized weights to get the answer.