# -*- coding: utf-8 -*-
"""Data1.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1nPDG8YKgABjWKTL1cRhMFXRTKRE4WnD2
"""

# Commented out IPython magic to ensure Python compatibility.
import pandas as pd
import numpy as np
import seaborn as sns
# %matplotlib inline 
import matplotlib.pyplot as plt
import sklearn 
import xgboost
from imblearn.over_sampling import SMOTE
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score,KFold,StratifiedKFold
from sklearn.metrics import confusion_matrix, accuracy_score,f1_score,precision_score,roc_auc_score

def transform_encode(data):
  """ removing outlier to do these we will use LocalOutlierfactor, any value tha
  t is less than one will be an outlier,the purpose of removing outliers is to prevent the model from 
  taking too long to load and misledding the model"""
  from scipy import stats
  from sklearn.preprocessing import StandardScaler, LabelEncoder,OneHotEncoder 
  from sklearn.neighbors import LocalOutlierFactor
  """duration was dropped because it has correlation with the target variable
  if duration is 0 then the customer might not subscribed, also this was done 
  so that it will not impact our outlier removal since it is not needed in training
  """
  data_1 = data.drop(['duration','y'],axis=1)
  numerical_df = data_1.select_dtypes(include=['int','float'])#selecting float and int columns
  list_numerical_df_columns = list(numerical_df.columns)
  """The localoutlierfactor is another model to detect outliers,
  any value that is less than 1 is considered an outlier since it dosen'
  follow the uniform distribution"""
  lof = LocalOutlierFactor()
  yhat = lof.fit_predict(numerical_df) #fitting the localoutlier factor model
  mask = yhat !=-1
  data = data.loc[mask,:]
  data_1 = data_1.loc[mask,:] #filtering out rows that are not outliers
  for col in list_numerical_df_columns:
    data_1[col] = StandardScaler().fit_transform(data_1[[col]]) #scaling the values so it can be on the same range
  cat_df = data_1.select_dtypes(include=['object'])
  cat_dumm = pd.get_dummies(cat_df) #converting the categorical data to 1 or 0
  """dropping the categorical columns becaue we have encoded and the old columns
   are not needed"""
  df = data_1.drop(list(cat_df.columns),axis=1)
  """concatenating the dataframe with the encoded categorical columns since we 
  had dropped the columns earlier"""
  df = pd.concat([df,cat_dumm],axis=1)
  #encoding the target variable y and renaming it to subscribed and joing it back 
  df['Subscribed'] = LabelEncoder().fit_transform(data['y'])
  return df

def reduce_dimension(data,reduction_model):
  """since our colummns are many, we need to reduce the computational time by 
  reducing the numbers of columns and still retaining useful columns, we will be using 
  principal component ananlysis,t-distributed stochastic neighbor and auto-encoders"""
  data_1 = transform_encode(data)
  data = data_1.drop(['Subscribed'],axis=1)
  """ importing necessary libraries"""
  from sklearn.decomposition import PCA 
  from sklearn.manifold import TSNE
  from keras.models import Model 
  from keras.layers import Input,Dense
  from keras import regularizers
  encoding_dim= 20
  if reduction_model == 'pca':
    pca = PCA(n_components=20) #components to reduce the columns to
    """ to justify why we choose 20 components from the plot we could see that 
    best components is 20 because that is where the lines starts to get constant"""
    pca_2 = PCA().fit(data.values)
    plt.plot(np.cumsum(pca_2.explained_variance_ratio_))
    plt.xlabel('number of components')
    plt.ylabel('cummulative explained variance')
    reduced_df = pd.DataFrame(pca.fit_transform(data.values),columns = ["principal component{}".format(str(i)) for i in range(1,21)])
  elif reduction_model=='tsne':
    """ tsne maximum components is 2 hence we will go with it"""
    tsne = TSNE(n_components=2,n_iter=300)
    reduced_df = pd.DataFrame(tsne.fit_transform(data),columns= ["tsne component{}".format(str(i)) for i in range(1,3)])
  else:
    # fixed dimensions
    input_dim = data.shape[1]
    encoding_dim = 20
    """ Number of neurons in each layer [data_columns which is input_dim,30 for 
    the first hidden layer,30 for the second hidden layer and 20 for our desired 
    output layer which is encoding dimension and it is 20]. Also for eah encoded layer we will be passing
    the output fromone layer to the other, hence the need to make one layer input connected to the next layer
    and our activation function will be tanh"""
    input_layer = Input(shape=(input_dim,))
    encoded_layer_1 = Dense(
        40,activation='tanh',activity_regularizer=regularizers.l1(10e-5))(input_layer)
    encoded_layer_2 = Dense(30,activation='tanh')(encoded_layer_1)
    encoder_layer_3 = Dense(encoding_dim,activation='tanh')(encoded_layer_2)
    # create encoder model
    encoder = Model(inputs=input_layer,outputs=encoder_layer_3)
    reduced_df= pd.DataFrame(encoder.predict(data)
    )
  print(reduced_df.shape)
  print(data_1[['Subscribed']].shape)
  reduced_df['Subscribed']=data_1['Subscribed'].values
  return reduced_df

