
import utilities
import data_preprocessing
from optparse import OptionGroup, OptionParser

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import AdaBoostClassifier
from sklearn.model_selection import cross_val_score
from sklearn.feature_selection import RFECV

def CreateAllProductHistograms ():
  """Creates every product ratio histogram.
  """
  productCodes = analyze_data.productHierarchy.product_module_code
  productCodes = productCodes.unique ().tolist ()

  for pc in productCodes:
    if pc >= 0:
      print ('Processing Product Code %d' % pc)
      data_preprocessing.GetHouseholdProductFrequencyByCode (int (pc), True)

def FitModels (models, productCode, cutOff, kFold, featureEvaluation, doPlot):
  """Fit an arbitrary number of models to the data and evaluate their
     performance in a boxplot.

  Keyword Arguments:
  models - List of models to fit to the data.
  productCode - products to evaluate the models on
  cutOff - the point at which we determine someone to be branded or non-branded
  kFold - number of folds to use for cross validation strategy
  featureEvaluation - if true, we will remove features recursively and evaluate which
                      are the best
  doPlot - whether we do the boxplot or not
  """
  (X, Y) = data_preprocessing.PrepareData (productCode, cutOff)

  names = []
  results = []

  for name, model in models:
    names.append (name)
    scores = None

    if featureEvaluation:
      rfecv = RFECV (estimator=model, step=1, cv=kFold, scoring='accuracy')
      rfecv.fit (X, Y.ratio.ravel ())
      scores = rfecv.grid_scores_

      print "Optimal Number of Features:"
      print rfecv.n_features_
      print "Feature Mask:"
      print rfecv.support_
      print "Feature Ranking:"
      print rfecv.ranking_

      if doPlot:
        fig = plt.figure ()
        plt.xlabel ("Number of Features Selected")
        plt.ylabel ("CV Score")
        plt.plot (range (1, len (rfecv.grid_scores_) + 1), rfecv.grid_scores_)
        plt.savefig (utilities.outputFolder + str (productCode) + '-' + \
                     name + '-' + 'feature-evaluation')
        plt.close (fig)

    else:
      scores = cross_val_score (model, X, Y.ratio.ravel (), cv=kFold, scoring='accuracy')

    results.append (scores)

    msg = "%s: %f (%f)" % (name, scores.mean(), scores.std())
    print (msg)

  if doPlot:
    fig = plt.figure ()
    fig.suptitle('Algorithm Comparison Product Code %s' % productCode)
    plt.boxplot (results)
    x = fig.add_subplot (111)
    x.set_xticklabels (names)
    plt.savefig (utilities.outputFolder + str (productCode) + '-algorithm-comparison')
    plt.close (fig)

def main ():
  parser = OptionParser ()

  #=========================General Group Start=========================#
  generalGroup = OptionGroup (parser, "General Options", "These options may be requirements for any other options.") 
  generalGroup.add_option ('-p', '--product-code', dest='product_code', type='string')
  generalGroup.add_option ('-c', '--cut-off', dest='cutoff', type=float, default=0.5)
  #=========================General Group End=========================#

  #=========================Model Group Start=========================#
  modelGroup = OptionGroup (parser, "Model Options", "These options control what models to run on the dataset.")

  modelGroup.add_option ('-k', '--k-fold', dest='k_fold', type=int, default=10)
  modelGroup.add_option ('--do-plots', dest='do_plots', action='store_true', default=False)
  modelGroup.add_option ('--run-svm', action='store_true', \
                         dest='run_svm', default=False)

  modelGroup.add_option ('--run-logistic', action='store_true', \
                         dest='run_logistic', default=False)

  modelGroup.add_option ('--run-ada-boost', action='store_true', \
                         dest='run_ada_boost', default=False)

  modelGroup.add_option ('--recursive-feature-evaluation', action='store_true', \
                         dest='recursive_feature_evaluation', default=False)
  #=========================Model Group End=========================#

  #=========================Utility Group Start=========================#
  utilityGroup = OptionGroup (parser, "Utility Options", \
                              "These options are meant to provide extra functionality " \
                              "such as creating histograms of the brand purchases for each household.")

  utilityGroup.add_option ('--create-histograms', action='store_true', \
                           dest='create_histograms', default=False)

  utilityGroup.add_option ('--create-single-histogram', action='store_true', \
                           dest='create_single_histogram', default=False)
  #=========================Utility Group End=========================#

  parser.add_option_group (generalGroup)
  parser.add_option_group (modelGroup)
  parser.add_option_group (utilityGroup)
  
  (options, args) = parser.parse_args ()

  utilities.ReadAllPickledObjects ()

  if options.create_histograms == True:
    CreateAllProductHistograms ()

  runModel = options.run_svm | options.run_logistic | options.run_ada_boost

  if runModel or options.create_single_histogram:
    if not options.product_code:
      parser.error ('Must provide a product code for any single product operations')

    if not options.cutoff and runModel:
      parser.error ('Must provide a cutoff for any single product operations')

    if options.create_single_histogram:
      GetHouseholdProductFrequencyByCode (options.product_code, True)

    models = []

    if options.run_svm == True:
      models.append (('SVM', SVC ()))

    if options.run_logistic == True:
      models.append (('Logistic Regression', LogisticRegression ()))

    if options.run_ada_boost == True:
      models.append (('AdaBoost', AdaBoostClassifier (n_estimators=200)))

    if len (models) > 0:
      FitModels (models, options.product_code, options.cutoff, options.k_fold, \
                 options.recursive_feature_evaluation, options.do_plots)

if __name__ == "__main__":
  main ()
