import streamlit as st
import pandas as pd
import joblib,os
import seaborn as sns
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_recall_fscore_support as score, mean_squared_error
from sklearn.metrics import confusion_matrix,accuracy_score
from nltk.tokenize import word_tokenize
from gensim.models.doc2vec import TaggedDocument
import nltk
from nltk.corpus import stopwords
from sklearn import preprocessing
from sklearn.feature_extraction.text import TfidfVectorizer
import matplotlib.pyplot as plt
import re
import warnings
import pickle
import webbrowser
from wordcloud import WordCloud
warnings.filterwarnings("ignore")
# Vectorizer
news_vectorizer = open("models\\Vectorizer", "rb")
news_cv = joblib.load(news_vectorizer)

#Loading Model
def load_prediction_model(model):
    loaded_model = joblib.load(open(os.path.join(model), "rb"))
    return loaded_model

# Get Category from Numeric Value
def get_category(val, dict):
    for key, value in dict.items():
        if val == value:
            return key

def add_parameter_ui(clf_name):
    params={}
    st.sidebar.write("Select values: ")

    if clf_name == "Logistic Regression":
        R = st.sidebar.slider("Regularization",0.1,10.0,step=0.1)
        MI = st.sidebar.slider("max_iter",50,400,step=50)
        params["R"] = R
        params["MI"] = MI

    elif clf_name == "KNN":
        K = st.sidebar.slider("n_neighbors",1,20)
        params["K"] = K

    elif clf_name == "SVM":
        C = st.sidebar.slider("Regularization",0.01,10.0,step=0.01)
        kernel = st.sidebar.selectbox("Kernel",("linear", "poly", "rbf", "sigmoid", "precomputed"))
        params["C"] = C
        params["kernel"] = kernel

    elif clf_name == "Decision Tree":
        M = st.sidebar.slider("max_depth", 2, 20)
        C = st.sidebar.selectbox("Criterion", ("gini", "entropy"))
        SS = st.sidebar.slider("min_samples_split",1,10)
        params["M"] = M
        params["C"] = C
        params["SS"] = SS

    return params


def get_classifier(clf_name,params):
    global clf
    if clf_name == "Logistic Regression":
        clf = LogisticRegression(C=params["R"],max_iter=params["MI"])

    elif clf_name == "KNN":
        clf = KNeighborsClassifier(n_neighbors=params["K"])

    elif clf_name == "SVM":
        clf = SVC(kernel=params["kernel"],C=params["C"])

    elif clf_name == "Decision Tree":
        clf = DecisionTreeClassifier(max_depth=params["M"],criterion=params["C"])

    elif clf_name == "Naive Bayes":
        clf = MultinomialNB()

    return clf

def process_text(text):
    text = text.lower().replace('\n',' ').replace('\r','').strip()
    text = re.sub(' +', ' ', text)
    text = re.sub(r'[^\w\s]','',text)


    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(text)
    filtered_sentence = [w for w in word_tokens if not w in stop_words]
    filtered_sentence = []
    for w in word_tokens:
        if w not in stop_words:
            filtered_sentence.append(w)

    text = " ".join(filtered_sentence)
    return text

def get_dataset():
    data = pd.read_csv(r"data\BBC News Train.csv")
    data['News_length'] = data['Text'].str.len()
    data['Text_parsed'] = data['Text'].apply(process_text)
    label_encoder = preprocessing.LabelEncoder()
    data['Category_target']= label_encoder.fit_transform(data['Category'])
    return data


def compute(Y_pred, Y_test):
    # Confusion Matrix
    cm = confusion_matrix(Y_test, Y_pred)
    class_label = ["business", "tech", "politics", "sport", "entertainment"]
    df_cm = pd.DataFrame(cm, index=class_label, columns=class_label)

    # Create a figure and axes
    fig, ax = plt.subplots(figsize=(12, 7.5))
    sns.heatmap(df_cm, annot=True, cmap='Pastel1', linewidths=2, fmt='d', ax=ax)
    ax.set_title("Confusion Matrix", fontsize=15)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")

    # Display the plot
    st.pyplot(fig)

    # Calculate Metrics
    acc = accuracy_score(Y_test, Y_pred)
    mse = mean_squared_error(Y_test, Y_pred)
    precision, recall, fscore, support = score(Y_test, Y_pred, average='weighted')

    st.subheader("Metrics of the model: ")
    st.text(
        f'Precision: {precision}\nRecall: {recall}\nF1-Score: {fscore}\nAccuracy: {acc * 100}%\nMean Squared Error: {mse}')


#Build Model
def model(clf):
    X_train,X_test,Y_train,Y_test=train_test_split(data['Text_parsed'],
                                                    data['Category_target'],test_size=0.2,random_state=65)
    ngram_range = (1,2)
    min_df = 10
    max_df = 1.
    max_features = 300
    tfidf = TfidfVectorizer(encoding='utf-8',
                        ngram_range=ngram_range,
                        stop_words=None,
                        lowercase=False,
                        max_df=max_df,
                        min_df=min_df,
                        max_features=max_features,
                        norm='l2',
                        sublinear_tf=True)

    features_train = tfidf.fit_transform(X_train).toarray()
    labels_train = Y_train


    features_test = tfidf.transform(X_test).toarray()
    labels_test = Y_test


    clf.fit(features_train, labels_train)
    Y_pred = clf.predict(features_test)
    acc=accuracy_score(labels_test,Y_pred)
    return clf, Y_test, Y_pred

#tokenize for nlp
def tokenize_text(text):
    tokens = []
    for sent in nltk.sent_tokenize(text):
        for word in nltk.word_tokenize(sent):
            if len(word) < 2:
                continue
            tokens.append(word.lower())
    return tokens

def vec_for_learning(model_dbow, tagged_docs):
    sents = tagged_docs.values
    targets, regressors = zip(*[(doc.tags[0], model_dbow.infer_vector(doc.words, epochs=20)) for doc in sents])

    return targets, regressors

data = get_dataset()
X = data['Text_parsed']
Y = data['Category_target']

def main():
    activities = ["About","Data", "Prediction","NLP"]
    choice = st.sidebar.selectbox("Choose Activity", activities)
    if choice=="Data":
        st.title('Data')
        st.write("The following is the DataFrame of the `BBC News` dataset.")
        data = pd.read_csv(r"data\BBC News Train.csv")
        st.write(data)
    if choice=="About":
        with st.container():
            st.title("Classifying News Articles Based on Their Headlines Using Machine Learning Algorithms")
            st.markdown(""" 
			#### Built with Streamlit by Temirlan Ibragimov
			""")
            url = 'https://github.com/bozzbala'
            if st.button('Github'):
                webbrowser.open_new_tab(url)

    if choice=="Prediction":

        st.info("Prediction with ML")
        news_text = st.text_area("Enter Text", "Type Here")
        all_ml_models = ["Logistic Regression", "Naive Bayes", "Decision Tree", "SVM", "KNN"]
        model_choice = st.selectbox("Choose ML Model", all_ml_models)
        prediction_labels = {'business':0, 'tech':1, 'politics':2, 'sport':3, 'entertainment':4}
        params = add_parameter_ui(model_choice)

        if st.button("Classify"):
            st.text("Original text ::\n{}".format(news_text))
            news_text = process_text(news_text)
            vect_text = news_cv.transform([news_text]).toarray()
            clf = get_classifier(model_choice,params)
            predictor, Y_pred,Y_test = model(clf)
            prediction = predictor.predict(vect_text)
            result = get_category(prediction, prediction_labels)
            st.success(result)
            st.markdown("<hr>",unsafe_allow_html=True)
            st.subheader(f"Classifier Used: {model_choice}")
            compute(Y_pred,Y_test)
            if st.checkbox("WordCloud"):
                st.subheader("WordCloud: ")
                c_text = news_text
                wordcloud = WordCloud().generate(c_text)
                plt.imshow(wordcloud, interpolation='bilinear')
                plt.axis("off")
                plt.show()
                st.pyplot()
    if choice == "NLP":
        st.info("Natural Language Processing")
        news_text = st.text_area("Enter Text", "Type Here")
        c_text = news_text.strip()
        df = pd.read_csv("data/BBC_News_Train_Processed.csv")

        if st.button("Classify"):
            prediction_labels = {0: 'business', 1: 'entertainment', 2: 'politics', 3: 'sport', 4: 'tech'}

            # Обработка текста
            news_text = process_text(news_text)
            news_text = pd.DataFrame({'Text': [news_text]})
            train, test = train_test_split(df, test_size=0.2, random_state=42)

            # Преобразование данных в TaggedDocument
            news_text = news_text.apply(lambda r: TaggedDocument(words=tokenize_text(r['Text']), tags=[0]), axis=1)
            test_tagged = test.apply(lambda r: TaggedDocument(words=tokenize_text(r['Text']), tags=[r.Category]),
                                     axis=1)

            # Загрузка моделей
            try:
                model_dbow = pickle.load(open('models/nlp_model_dbow.sav', 'rb'))
                model_logistic = pickle.load(open('models/nlp_model.sav', 'rb'))
            except FileNotFoundError:
                st.error("Model files not found. Please check the 'models' directory.")
                return

            # Векторизация текстов
            try:
                Y_text, X_text = vec_for_learning(model_dbow, news_text)
                Y_test, X_test = vec_for_learning(model_dbow, test_tagged)

                # Предсказания
                Y_pred = model_logistic.predict(X_test)
                Y_text_pred = model_logistic.predict(X_text)

                result = prediction_labels[Y_text_pred[0]]
                st.success(result)

                # Вывод метрик
                st.markdown("<hr>", unsafe_allow_html=True)
                st.subheader("Classifier Used: NLP with logistic regression")
                compute(Y_pred, Y_test)

                # Визуализация WordCloud
                st.subheader("WordCloud:")
                wordcloud = WordCloud().generate(c_text)
                plt.imshow(wordcloud, interpolation='bilinear')
                plt.axis("off")
                st.pyplot()
            except Exception as e:
                st.error(f"Error during classification: {e}")


if __name__ == '__main__':
    main()