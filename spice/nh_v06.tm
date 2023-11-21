KPL/MK

   This meta-kernel lists the NH SPICE kernels providing coverage
   from around 19 March, 2007 through 30 December, 2019.

   All of the kernels listed below are archived in the NH SPICE data
   set (DATA_SET_ID = "NH-J/P/SS-SPICE-6-V1.0"). This set of files and
   the order in which they are listed were picked to provide the best
   available data and the most complete coverage based on the
   information about the kernels available at the time this meta-kernel
   was made. For detailed information about the kernels listed below
   refer to the internal comments included in the kernels and the
   documentation accompanying the NH SPICE data set.
 
   It is recommended that users make a local copy of this file and
   modify the value of the PATH_VALUES keyword to point to the actual
   location of the NH SPICE data set's ``data'' directory on their
   system. Replacing ``/'' with ``\'' and converting line terminators
   to the format native to the user's system may also be required if
   this meta-kernel is to be used on a non-UNIX workstation.
 
   This file was created ca. April, 2020 by Brian Enke of SwRI.

   The original name of this file was nh_v06.tm.

   \begindata

      PATH_VALUES       = (
                           './data'
                          )
      PATH_SYMBOLS      = (
                           'KERNELS'
                          )
      KERNELS_TO_LOAD   = ('$KERNELS/lsk/naif0012.tls',

                           '$KERNELS/pck/pck00010.tpc',
                           '$KERNELS/pck/nh_stars_kbo_centaur_v003.tpc',
                           '$KERNELS/pck/nh_pcnh_008.tpc',

                           '$KERNELS/sclk/new_horizons_2132.tsc',

                           '$KERNELS/fk/nh_v220.tf',
                           '$KERNELS/fk/nh_soc_misc_v002.tf',
                           '$KERNELS/fk/heliospheric_v004u.tf',

                           '$KERNELS/ik/nh_alice_v200.ti',
                           '$KERNELS/ik/nh_lorri_v201.ti',
                           '$KERNELS/ik/nh_pepssi_v110.ti',
                           '$KERNELS/ik/nh_ralph_v100u.ti',
                           '$KERNELS/ik/nh_rex_v100.ti',
                           '$KERNELS/ik/nh_sdc_v101.ti',
                           '$KERNELS/ik/nh_swap_v200.ti',

                           '$KERNELS/spk/nh_de433_od147.bsp',
                           '$KERNELS/spk/jup260.bsp',
                           '$KERNELS/spk/kbo_centaur_20170422.bsp',
                           '$KERNELS/spk/kbo_centaur_20131129.bsp',
                           '$KERNELS/spk/kbo_centaur_20200430.bsp',
                           '$KERNELS/spk/nh_extras.bsp',
                           '$KERNELS/spk/nh_stars.bsp',
                           '$KERNELS/spk/sb_2002jf56_2.bsp',
                           '$KERNELS/spk/nh_2014_mu69_od147.bsp',
                           '$KERNELS/spk/nh_nep_ura_000.bsp',
                           '$KERNELS/spk/nh_plu017.bsp',
                           '$KERNELS/spk/nh_plu047_od122.bsp',

                           '$KERNELS/spk/nh_pred_alleph_od151.bsp',

                           '$KERNELS/spk/nh_recon_e2j_v1.bsp',
                           '$KERNELS/spk/nh_recon_j2sep07_prelimv1.bsp',
                           '$KERNELS/spk/nh_recon_od077_v01.bsp',
                           '$KERNELS/spk/nh_recon_od117_v01.bsp',
                           '$KERNELS/spk/nh_recon_pluto_od122_v01.bsp',
                           '$KERNELS/spk/nh_recon_arrokoth_od147_v01.bsp',

                           '$KERNELS/ck/merged_nhpc_2006_v011.bc',
                           '$KERNELS/ck/merged_nhpc_2007_v006.bc',
                           '$KERNELS/ck/merged_nhpc_2008_v001.bc',
                           '$KERNELS/ck/merged_nhpc_2009_v001.bc',
                           '$KERNELS/ck/merged_nhpc_2010_v001.bc',
                           '$KERNELS/ck/merged_nhpc_2011_v001.bc',
                           '$KERNELS/ck/merged_nhpc_2012_v001.bc',
                           '$KERNELS/ck/merged_nhpc_2013_v001.bc',
                           '$KERNELS/ck/merged_nhpc_2014_v001.bc',
                           '$KERNELS/ck/merged_nhpc_2015_v039.bc',
                           '$KERNELS/ck/merged_nhpc_2016_v003.bc',
                           '$KERNELS/ck/merged_nhpc_2017_v014.bc',
                           '$KERNELS/ck/merged_nhpc_2018_v100.bc',
                           '$KERNELS/ck/merged_nhpc_2019_v018.bc'
                          )


   \begintext
