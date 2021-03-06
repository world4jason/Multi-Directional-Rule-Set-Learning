import os
from typing import List, Dict, Tuple

from dask import delayed
from dask.delayed import Delayed
from distributed import Client

from experiments.dask_utils.computations import compute_delayed_functions
from experiments.dask_utils.dask_initialization import reconnect_client_to_ssh_cluster

from experiments.e1_st_association_vs_tree_rules.model_evaluation.evaluate_single_target_mids_model import \
    evaluate_single_target_mids_model_for_dataset_fold

# --- NAMING ---
from experiments.e1_st_association_vs_tree_rules.file_naming.single_target_filtered_mids_naming import (
    get_single_target_tree_mids_clf_relative_file_name, assoc_vs_tree_based_single_target_mids_clf_dir,
    get_single_target_filtered_tree_mids_clf_abs_file_name,
    get_single_target_filtered_tree_mids_target_attr_to_score_info_abs_file_name,
    get_single_target_filtered_tree_mids_interpret_stats_abs_file_name
)
from experiments.file_naming.single_target_classifier_indicator import SingleTargetClassifierIndicator
# --------------


TargetAttr = str


def main():
    from experiments.arcbench_data_preparation.dataset_info import datasets
    datasets = [dict(filename="iris", targetvariablename="class", numerical=True)]
    from experiments.dask_utils.dask_initialization import scheduler_host_name
    scheduler_host: str = scheduler_host_name
    list_of_computations: List[Tuple[Delayed, Dict]] = []

    confidence_boundary_values: List[float] = [0.75, 0.95]
    min_support = 0.1
    max_depth = 7

    nb_of_folds: int = 10

    use_dask = False
    if use_dask:
        client: Client = reconnect_client_to_ssh_cluster(scheduler_host)

    for dataset_info in datasets:
        dataset_name = dataset_info['filename']
        target_attribute: str = dataset_info['targetvariablename']
        for fold_i in range(nb_of_folds):
            for confidence_boundary_val in confidence_boundary_values:

                classifier_indicator = SingleTargetClassifierIndicator.random_forest

                relative_name: str = get_single_target_tree_mids_clf_relative_file_name(
                    dataset_name=dataset_name, fold_i=fold_i,
                    target_attribute=target_attribute,
                    classifier_indicator=classifier_indicator,
                    confidence_boundary_val=confidence_boundary_val,
                    min_support=min_support, max_depth=max_depth,
                )
                log_file_dir: str = assoc_vs_tree_based_single_target_mids_clf_dir()

                logger_name: str = f'evaluate_single_target_tree_mids_' + relative_name
                logger_file_name: str = os.path.join(
                    log_file_dir,
                    f'{relative_name}_model_evaluation_single_target_tree_mids.log'
                )

                mids_classifier_abs_file_name: str = get_single_target_filtered_tree_mids_clf_abs_file_name(
                    dataset_name=dataset_name, fold_i=fold_i,
                    target_attribute=target_attribute,
                    classifier_indicator=classifier_indicator,
                    min_support=min_support, max_depth=max_depth,
                    confidence_boundary_val=confidence_boundary_val
                )

                mids_target_attr_to_score_info_abs_file_name: str = \
                    get_single_target_filtered_tree_mids_target_attr_to_score_info_abs_file_name(
                        dataset_name=dataset_name, fold_i=fold_i,
                        target_attribute=target_attribute,
                        classifier_indicator=classifier_indicator,
                        min_support=min_support, max_depth=max_depth,
                        confidence_boundary_val=confidence_boundary_val
                    )

                mids_interpret_stats_abs_file_name: str = get_single_target_filtered_tree_mids_interpret_stats_abs_file_name(
                    dataset_name=dataset_name, fold_i=fold_i,
                    target_attribute=target_attribute,
                    classifier_indicator=classifier_indicator,
                    min_support=min_support, max_depth=max_depth,
                    confidence_boundary_val=confidence_boundary_val
                )

                if use_dask:
                    func_args = dict(
                        dataset_name=dataset_name, fold_i=fold_i,
                        logger_name=logger_name,
                        logger_file_name=logger_file_name,
                        mids_classifier_abs_file_name=mids_classifier_abs_file_name,
                        mids_target_attr_to_score_info_abs_file_name=mids_target_attr_to_score_info_abs_file_name,
                        mids_interpret_stats_abs_file_name=mids_interpret_stats_abs_file_name
                    )

                    delayed_func = \
                        delayed(evaluate_single_target_mids_model_for_dataset_fold)(
                            **func_args
                        )
                    list_of_computations.append((delayed_func, func_args))
                else:
                    evaluate_single_target_mids_model_for_dataset_fold(
                        dataset_name=dataset_name, fold_i=fold_i,
                        logger_name=logger_name,
                        logger_file_name=logger_file_name,
                        mids_classifier_abs_file_name=mids_classifier_abs_file_name,
                        mids_target_attr_to_score_info_abs_file_name=mids_target_attr_to_score_info_abs_file_name,
                        mids_interpret_stats_abs_file_name=mids_interpret_stats_abs_file_name
                    )

    if use_dask:
        log_file_dir: str = assoc_vs_tree_based_single_target_mids_clf_dir()

        logger_name: str = f'evaluate_single_target_tree_mids_ERROR_LOGGER'
        logger_file_name: str = os.path.join(
            log_file_dir,
            f'ERROR_LOG_model_evaluation_single_target_tree_mids.log'
        )

        compute_delayed_functions(
            list_of_computations=list_of_computations,
            client=client,
            nb_of_retries_if_erred=5,
            error_logger_name=logger_name,
            error_logger_file_name=logger_file_name
        )


if __name__ == '__main__':
    main()
