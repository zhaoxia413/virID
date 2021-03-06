//============================================================================//
// Default params
//============================================================================//
params.blast_database = "/n/data2/dfci/medonc/decaprio/jason/\
genomes_indexes_references_databases/blastn_databases/nt_v5/nt_v5"
params.blast_evalue = 10
params.blast_outfmt = "6 qseqid stitle sseqid staxid evalue bitscore pident length"
params.blast_log_file = ""
params.blast_type = "megablast"
params.blast_max_hsphs = 1
params.blast_max_targets = 30
params.blast_restrict_to_taxids = "no"
params.blast_ignore_taxids = "no"
params.out_dir = 'output'
params.log_file = "${workflow.launchDir}/${params.out_dir}/reports/virID.log"

//============================================================================//
// Define process
//============================================================================//
process blast {
  tag "$sampleID"
  publishDir "$params.out_dir/blast", mode: "copy"
  beforeScript "module load gcc conda2"

  input:
  tuple sampleID, sequences

  output:
  tuple sampleID, file("*_blast.out")

  script:
  if( (params.blast_restrict_to_taxids != "no") && (params.blast_ignore_taxids != "no") )
    error "Only one of params.blast_restrict_to_taxids or \
    params.blast_ignore_taxids may be entered."

  else
      """
      $workflow.projectDir/bin/bash/run_BLASTN.sh \
      -d ${params.blast_database} \
      -q ${sequences} \
      -o ${sampleID}_blast.out \
      -t ${task.cpus} \
      -e ${params.blast_evalue} \
      -f "${params.blast_outfmt}" \
      -l ${params.blast_log_file} \
      -b ${params.blast_type} \
      -m ${params.blast_max_hsphs} \
      -s ${params.blast_max_targets} \
      -r ${params.blast_restrict_to_taxids} \
      -i ${params.blast_ignore_taxids} \
      -n ${sampleID}
      """
}
