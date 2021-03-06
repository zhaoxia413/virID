#!/usr/bin/env python3

import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import argparse
import os
import pathlib

def str2bool(v):
    """
    Function to read in argparse booleans. From Maxim/Knight71 on stackoverflow
    - see https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse
    """
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def generate_heatmap(df,
    level,
    non_sample_cols,
    TOP_NUMBER_OF_ROWS=50,
    superkingdom="all",
    cluster_samples=True,
    cluster_taxa=True):

    # Sort for specified level and only viruses if specified
    if superkingdom == "Virus":
        rows = (df.superkingdom.isin(['sk__Viruses', 'Viruses']) & df.level.isin([level]))
    elif superkingdom == "Bacteria":
        rows = (df.superkingdom.isin(['sk__Bacteria', 'Bacteria']) & df.level.isin([level]))
    elif superkingdom == "all":
        rows = (df.level.isin([level]))
    else:
        raise ValueError("Superkingdom value must be 'Virus', 'Bacteria', or 'all'." +
        " You entered {}".format(superkingdom))

    df = df[rows]

    # Get sample cols
    sample_cols = [colname for colname in df.columns.to_list() if colname not in non_sample_cols]

    # Take the top rows by mean
    df['agg_mean'] = df[sample_cols].mean(axis=1)
    df = df.sort_values('agg_mean', ascending = False).head(TOP_NUMBER_OF_ROWS)
    df = df.drop(labels=['agg_mean'], axis=1)

    # Condense the numbers by taking log2 of everything, and replace
    # negative infinity with 0
    df[sample_cols] = df[sample_cols].apply(np.log10).replace(np.NINF, 0)

    # Remove columns that only have 0s
    df = df.loc[:, (df != 0).any(axis=0)]

    # Need to find the sample_cols again, because some removed
    sample_cols = [col for col in sample_cols if col in df.columns.to_list()]

    # If DF is empty, i.e. no taxa met the conditions, return a notice.
    if len(df) == 0:
        print("The dataframe is of size zero.")
        print("There may be no taxa of the superkingdom, or no taxa of the given level.")
        print("level: {0}, superkingdom:{1}".format(level, superkingdom))
        return ''

    # If DF is only one row, can't do clustermap, do regular heatmap
    if len(df) == 1:
        print("There is only one taxa. Reporting a heatmap.")
        heatmap = sns.heatmap(df[sample_cols],
            cmap="Blues",
            yticklabels=True
        )
        return heatmap

    # Get a color palette to map to superkingdom status
    network_pal = sns.color_palette('coolwarm', len(df.superkingdom.unique()))
    network_lut = dict(zip(df.superkingdom.unique(), network_pal))
    networks = df.superkingdom
    network_colors = pd.Series(networks).map(network_lut)

    # Plot!
    cluster_map = sns.clustermap(df[sample_cols],
                   cmap="Blues",
                   cbar_kws={'label': 'Log10 Number of Reads'},
                   row_colors=network_colors,
                   yticklabels=True,
                   col_cluster=cluster_samples,
                   row_cluster=cluster_taxa
                   )
    plt.setp(cluster_map.ax_heatmap.yaxis.get_majorticklabels(), rotation=0)
    plt.setp(cluster_map.ax_heatmap.set_yticklabels(cluster_map.ax_heatmap.get_ymajorticklabels(), fontsize = 8))
    plt.setp(cluster_map.ax_heatmap.set_xticklabels(cluster_map.ax_heatmap.get_xmajorticklabels(), fontsize = 8))
    plt.setp(cluster_map.ax_heatmap.set(xlabel='Samples (Note: It is possible not all are labeled!)', ylabel='Taxa'))
    return cluster_map

def save_heatmap(heatmap, output_path):
    # If there is no heatmap, don't do anything
    if heatmap == '':
        return
    else:
        try:
            heatmap.savefig(output_path)
        except AttributeError:
            heatmap.get_figure().savefig(output_path)

def main():
    #---------------------------------------------------------------------------#
    # Parse inputs
    #---------------------------------------------------------------------------#
    parser = argparse.ArgumentParser(description="""
    The purpose of this script is to generate heatmaps from an input virID
    or PathSeq aggregated hit table.
    """)

    parser.add_argument(
        "-i",
        "--input_df",
        type=str,
        required=True,
        help='''Path to the input hit table.''',
    )
    parser.add_argument(
        "-f",
        "--input_format",
        type=str,
        required=True,
        help='''Format of the infile.. Options are "virID" or "pathseq".''',
    )
    parser.add_argument(
        "-o",
        "--output_prefix",
        type=str,
        required=True,
        help='''Prefix/path to the output heatmaps.''',
    )
    parser.add_argument(
        "-t",
        "--TOP_NUMBER_OF_ROWS",
        type=int,
        required=True,
        help='''Top number of taxa to display (based on mean abundance).''',
    )
    parser.add_argument(
        "-r",
        "--remove_suffix",
        type=str,
        required=False,
        default="",
        help='''A suffix to remove from the column names.''',
    )
    parser.add_argument(
        "-F",
        "--output_format",
        type=str,
        required=False,
        default='pdf',
        help='''
        Format the output heatmaps be in. Options are "pdf", "svg",
        "png", or any other matplotlib acceptable format.
        ''',
    )
    parser.add_argument(
        "-c",
        "--cluster_samples",
        type=str2bool,
        required=False,
        default=True,
        help='''
        Whether or not do heirarchecially cluster the samples (columns). True,
        true, t, and similar iterations of False are acceptable inputs.
        ''',
    )
    parser.add_argument(
        "-C",
        "--cluster_taxa",
        type=str2bool,
        required=False,
        default=True,
        help='''
        Whether or not do heirarchecially cluster the taxa (rows). True, true,
        t, and similar iterations of False are acceptable inputs.
        ''',
    )


    args = parser.parse_args()
    input_df = args.input_df
    input_format = args.input_format
    output_prefix = args.output_prefix
    TOP_NUMBER_OF_ROWS = args.TOP_NUMBER_OF_ROWS
    remove_suffix = args.remove_suffix
    output_format = args.output_format
    cluster_samples=args.cluster_samples
    cluster_taxa=args.cluster_taxa

    #------------------------------------------------------------------------------#
    # Setting defaults
    #------------------------------------------------------------------------------#
    print("Starting pyscript.")
    print("Detected an input format of {0}".format(input_format))
    if input_format.lower() == "pathseq":
        non_sample_cols = ["tax_id", "taxonomy", "type", "name", "kingdom", "reference_length"]
        taxonID = 'tax_id'
        lineage = 'taxonomy'
        level = 'type'
        superkingdom = 'kingdom'
        taxon = 'name'
    elif input_format.lower() == "virid":
        non_sample_cols = ["lineage", "superkingdom", "taxon", "level", "taxonID"]
        taxonID = 'taxonID'
        lineage = 'lineage'
        level = 'level'
        superkingdom = 'superkingdom'
        taxon = 'taxon'
    else:
        raise ValueError("sample_format must be {0} or {1}".format("pathseq", "virID"))

    # will use one column as the input index. Need to remove from non_sample_cols
    index_col = taxon
    non_sample_cols.remove(index_col)

    # import data
    print("Importing data.")
    df = pd.read_csv(input_df, sep="\t", index_col = False).set_index(index_col)

    # Remove suffix's if necessary
    df.columns = [column.replace(remove_suffix, "") for column in df.columns.to_list()]

    # if format is pathseq, rename 'kingdom' to 'superkingdom' and 'type' to 'level'
    if input_format == "pathseq":
        df = df.rename({'kingdom':'superkingdom', 'type':'level'}, axis='columns')
        non_sample_cols = ['superkingdom' if item == 'kingdom' else item for item in non_sample_cols]
        non_sample_cols = ['level' if item == 'type' else item for item in non_sample_cols]

    # generate heatmaps
    print("Generating heatmaps.")
    heatmap_viral_genera = generate_heatmap(df,
                                'genus',
                                non_sample_cols,
                                TOP_NUMBER_OF_ROWS=TOP_NUMBER_OF_ROWS,
                                superkingdom="Virus",
                                cluster_samples=cluster_samples,
                                cluster_taxa=cluster_taxa
                                )
    heatmap_viral_species = generate_heatmap(df,
                                'species',
                                non_sample_cols,
                                TOP_NUMBER_OF_ROWS=TOP_NUMBER_OF_ROWS,
                                superkingdom="Virus",
                                cluster_samples=cluster_samples,
                                cluster_taxa=cluster_taxa
                                )
    heatmap_viral_family = generate_heatmap(df,
                                'family',
                                non_sample_cols,
                                TOP_NUMBER_OF_ROWS=TOP_NUMBER_OF_ROWS,
                                superkingdom="Virus",
                                cluster_samples=cluster_samples,
                                cluster_taxa=cluster_taxa
                                )

    heatmap_bacteria_genera = generate_heatmap(df,
                                'genus',
                                non_sample_cols,
                                TOP_NUMBER_OF_ROWS=TOP_NUMBER_OF_ROWS,
                                superkingdom="Bacteria",
                                cluster_samples=cluster_samples,
                                cluster_taxa=cluster_taxa
                                )
    heatmap_bacteria_species = generate_heatmap(df,
                                'species',
                                non_sample_cols,
                                TOP_NUMBER_OF_ROWS=TOP_NUMBER_OF_ROWS,
                                superkingdom="Bacteria",
                                cluster_samples=cluster_samples,
                                cluster_taxa=cluster_taxa
                                )

    heatmap_all_genera = generate_heatmap(df,
                            'genus',
                            non_sample_cols,
                            TOP_NUMBER_OF_ROWS=TOP_NUMBER_OF_ROWS,
                            superkingdom="all",
                            cluster_samples=cluster_samples,
                            cluster_taxa=cluster_taxa
                            )
    heatmap_all_species = generate_heatmap(df,
                            'species',
                            non_sample_cols,
                            TOP_NUMBER_OF_ROWS=TOP_NUMBER_OF_ROWS,
                            superkingdom="all",
                            cluster_samples=cluster_samples,
                            cluster_taxa=cluster_taxa
                            )

    # Make output dir if needed
    output_directory = os.path.dirname(output_prefix)
    pathlib.Path(output_directory).mkdir(parents=True, exist_ok=True)

    # Write heatmaps to output
    print("Writing heatmaps.")
    save_heatmap(heatmap_viral_genera, output_prefix + "_viral_genera." + output_format)
    save_heatmap(heatmap_viral_species, output_prefix + "_viral_species." + output_format)
    save_heatmap(heatmap_viral_family, output_prefix + "_viral_family." + output_format)
    save_heatmap(heatmap_bacteria_genera, output_prefix + "_bacterial_genera." + output_format)
    save_heatmap(heatmap_bacteria_species, output_prefix + "_bacterial_species." + output_format)
    save_heatmap(heatmap_all_genera, output_prefix + "_all_genera." + output_format)
    save_heatmap(heatmap_all_species, output_prefix + "_all_species." + output_format)

    print("Finished.")

if __name__ == '__main__':
    main()
