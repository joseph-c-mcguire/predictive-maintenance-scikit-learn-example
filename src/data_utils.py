import logging
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import shap
from sklearn.base import BaseEstimator
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.metrics import classification_report, roc_auc_score
from yaml import load, Loader
from typing import List, Tuple, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config(file_path: str) -> Dict[str, Any]:
    """
    Load the configuration file from a YAML file.

    Parameters:
    file_path (str): Path to the YAML file.

    Returns:
    dict: Loaded configuration.

    Example:
    >>> config = load_config("config.yaml")
    >>> print(config)
    """
    logger.info(f"Loading configuration from {file_path}")
    with open(file_path, 'r') as file:
        config = load(file, Loader=Loader)
    logger.info("Configuration loaded successfully")
    return config

def load_data(file_path: str) -> pd.DataFrame:
    """
    Load the dataset from a CSV file.

    Parameters:
    file_path (str): Path to the CSV file.

    Returns:
    pd.DataFrame: Loaded dataset.

    Example:
    >>> data = load_data("data/dataset.csv")
    >>> print(data.head())
    """
    logger.info(f"Loading data from {file_path}")
    data = pd.read_csv(file_path)
    logger.info("Data loaded successfully")
    return data

def preprocess_data(data: pd.DataFrame, columns_to_drop: List[str] = None, columns_to_scale: List[str] = None, columns_to_encode: List[str] = None) -> Tuple[ColumnTransformer, np.ndarray]:
    """
    Preprocess the dataset: handle missing values, outliers, and normalize the data.

    Parameters:
    data (pd.DataFrame): Raw dataset.
    columns_to_drop (list[str], optional): List of columns to drop from the dataset. Defaults to None.
    columns_to_scale (list[str], optional): List of columns to scale/normalize. Defaults to None.
    columns_to_encode (list[str], optional): List of columns to encode (e.g., categorical columns). Defaults to None.

    Returns:
    Tuple[ColumnTransformer, pd.DataFrame]: Preprocessor and preprocessed dataset.

    Example:
    >>> preprocessor, preprocessed_data = preprocess_data(data, columns_to_drop=["col1"], columns_to_scale=["col2"], columns_to_encode=["col3"])
    >>> print(preprocessed_data.head())
    """
    logger.info("Starting data preprocessing")
    if columns_to_drop is None:
        columns_to_drop = []
    if columns_to_scale is None:
        columns_to_scale = []
    if columns_to_encode is None:
        columns_to_encode = []

    # Create a column transformer
    preprocessor = ColumnTransformer(
        transformers=[
            ('drop_columns', 'drop', columns_to_drop),
            ('scale_columns', StandardScaler(), columns_to_scale),
            ('encode_columns', OneHotEncoder(), columns_to_encode)
        ]
    )
    # Fit the column transformer
    scaled_data = preprocessor.fit_transform(data)
    logger.info("Data preprocessing completed")
    return preprocessor, scaled_data

def perform_eda(data: pd.DataFrame) -> None:
    """
    Perform exploratory data analysis on the dataset.

    Parameters:
    data (pd.DataFrame): Preprocessed dataset.

    Returns:
    None

    Example:
    >>> perform_eda(data)
    """
    logger.info("Starting exploratory data analysis (EDA)")
    # Plot histograms for each feature
    data.hist(bins=50, figsize=(20, 15))
    plt.show()

    # Plot heatmap of feature correlations
    plt.figure(figsize=(12, 8))
    sns.heatmap(data.corr(), annot=True, cmap='coolwarm')
    plt.show()
    logger.info("EDA completed")

def select_features(X: pd.DataFrame, y: pd.Series, preprocessor: ColumnTransformer) -> List[int]:
    """
    Select the most relevant features using a Random Forest model.

    Parameters:
    X (pd.DataFrame): Features.
    y (pd.Series): Target variable.
    preprocessor (ColumnTransformer): Preprocessor for the data.

    Returns:
    List[str]: Selected features.

    Example:
    >>> selected_features = select_features(X, y, preprocessor)
    >>> print(selected_features)
    """
    logger.info("Starting feature selection")
    processed_data = preprocessor.fit_transform(X)
    model = RandomForestClassifier()
    model.fit(processed_data, y)

    # Get feature importances
    selected_features = get_top_n_indices(model.feature_importances_)
    logger.info("Feature selection completed")
    return selected_features

def train_and_evaluate_model(X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Dict[str, Any]]:
    """
    Train and evaluate multiple machine learning models.

    Parameters:
    X_train (np.ndarray): Training features.
    y_train (np.ndarray): Training target.
    X_test (np.ndarray): Testing features.
    y_test (np.ndarray): Testing target.

    Returns:
    dict: Model evaluation results.

    Example:
    >>> results = train_and_evaluate_model(X_train, y_train, X_test, y_test)
    >>> for model_name, result in results.items():
    >>>     print(f"Model: {model_name}")
    >>>     print(result['Classification Report'])
    >>>     print(f"ROC AUC: {result['ROC AUC']}\n")
    """
    logger.info("Starting model training and evaluation")
    models = {
        'Logistic Regression': LogisticRegression(),
        'Decision Tree': DecisionTreeClassifier(),
        'Random Forest': RandomForestClassifier(),
        'Gradient Boosting': GradientBoostingClassifier(),
        'SVM': SVC(probability=True)
    }

    results = {}

    for name, model in models.items():
        logger.info(f"Training {name}")
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]

        results[name] = {
            'Classification Report': classification_report(y_test, y_pred),
            'ROC AUC': roc_auc_score(y_test, y_proba)
        }
        logger.info(f"Evaluation of {name} completed")

    logger.info("Model training and evaluation completed")
    return results

def tune_model(model: BaseEstimator, param_grid: dict, X_train: pd.DataFrame, y_train: pd.Series) -> BaseEstimator:
    """
    Perform hyperparameter tuning using GridSearchCV.

    Parameters:
    model (BaseEstimator): The machine learning model to be tuned.
    param_grid (dict): Hyperparameter grid.
    X_train (pd.DataFrame): Training features.
    y_train (pd.Series): Training target.

    Returns:
    BaseEstimator: Best estimator after hyperparameter tuning.

    Example:
    >>> from sklearn.ensemble import RandomForestClassifier
    >>> param_grid = {'n_estimators': [100, 200], 'max_depth': [10, 20]}
    >>> best_model = tune_model(RandomForestClassifier(), param_grid, X_train, y_train)
    """
    logger.info(f"Starting hyperparameter tuning for {model.__class__.__name__}")
    grid_search = GridSearchCV(
        estimator=model, param_grid=param_grid, cv=5, scoring='roc_auc', n_jobs=-1)
    grid_search.fit(X_train, y_train)
    logger.info(f"Hyperparameter tuning for {model.__class__.__name__} completed")

    return grid_search.best_estimator_

def interpret_model(model: BaseEstimator, X: pd.DataFrame) -> None:
    """
    Interpret the machine learning model using SHAP values.

    Parameters:
    model (BaseEstimator): Trained machine learning model.
    X (pd.DataFrame): Features for interpretation.

    Returns:
    None

    Example:
    >>> from sklearn.ensemble import RandomForestClassifier
    >>> model = RandomForestClassifier().fit(X_train, y_train)
    >>> interpret_model(model, X_test)
    """
    logger.info(f"Starting model interpretation for {model.__class__.__name__}")
    explainer = shap.Explainer(model)
    shap_values = explainer(X)

    # Summary plot
    shap.summary_plot(shap_values, X)
    logger.info(f"Model interpretation for {model.__class__.__name__} completed")

def monitor_model_performance(model: BaseEstimator, X: pd.DataFrame, y: pd.Series) -> float:
    """
    Monitor the performance of the deployed model.

    Parameters:
    model (BaseEstimator): Trained machine learning model.
    X (pd.DataFrame): Features.
    y (pd.Series): Target variable.

    Returns:
    float: ROC AUC score of the model on new data.

    Example:
    >>> from sklearn.ensemble import RandomForestClassifier
    >>> model = RandomForestClassifier().fit(X_train, y_train)
    >>> roc_auc = monitor_model_performance(model, X_test, y_test)
    >>> print(roc_auc)
    """
    logger.info(f"Monitoring performance of {model.__class__.__name__}")
    y_proba = model.predict_proba(X)[:, 1]
    roc_auc = roc_auc_score(y, y_proba)
    logger.info(f"Performance monitoring completed with ROC AUC: {roc_auc}")

    return roc_auc

def get_top_n_indices(arr: np.ndarray, n: int = 10) -> np.ndarray:
    """
    Get the indices of the n largest elements from a numpy array.

    Parameters:
    arr (np.ndarray): Input array.
    n (int): Number of top elements to retrieve indices for. Defaults to 10.

    Returns:
    np.ndarray: Array of indices of the n largest elements.

    Example:
    >>> arr = np.array([1, 3, 5, 7, 9, 2, 4, 6, 8, 0])
    >>> top_indices = get_top_n_indices(arr, 3)
    >>> print(top_indices)
    """
    logger.info(f"Getting top {n} indices from array")
    if n >= len(arr):
        return np.argsort(arr)[-n:][::-1]

    # Get the indices that would sort the array
    sorted_indices = np.argsort(arr)
    # Select the last n indices and reverse them
    top_n_indices = sorted_indices[-n:][::-1]
    logger.info(f"Top {n} indices obtained")

    return top_n_indices
