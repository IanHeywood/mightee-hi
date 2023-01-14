import glob
import os

mslist = glob.glob('*.ms')

for myms in mslist:
	myms = '1601667467_sdp_l0.32k.ms'

	bands = [('0:960~1150MHz','LOW'),
		('0:1290~1520MHz','MID'),
		('0:1610~1650MHz','HIGH')]


	tb.open(myms+'::FIELD')
	field_names = tb.getcol('NAME')
	tb.done()

	tb.open(myms+'::STATE')
	states = tb.getcol('OBS_MODE').tolist()
	target_state = states.index('TARGET')
	tb.done()

	tb.open(myms)
	subtab = tb.query(query='STATE_ID=='+str(target_state))
	target_id = list(set(subtab.getcol('FIELD_ID')))[0]
	target_name = field_names[target_id]
	target_scans = list(set(subtab.getcol('SCAN_NUMBER')))
	tb.done()

	scan_selection = ','.join(str(tt) for tt in target_scans)

	for band in bands:
		opdir = band[1]
		if not os.path.isdir(opdir):
			os.mkdir(opdir)
		spw_selection = band[0]
		opms = myms.replace('.ms','_'+target_name+'_'+band[1]+'.mms')
		if band[1] == 'LOW':
			average_chans = True
			chan_bin = 4
		else:
			average_chans = False
			chan_bin = 1
		mstransform(vis = myms,
			outputvis = opms,
			field = str(target_id),
			scan = scan_selection,
			spw = spw_selection,
			datacolumn = 'DATA',
			usewtspectrum = True,
			realmodelcol = True,
			chanaverage = average_chans,
			chanbin = chan_bin,
			createmms = True,
			separationaxis = 'scan',
			numsubms = len(target_scans),
			hanning = False,
			regridms = True,
			mode = 'channel',
			outframe = 'BARY',
			interpolation = 'nearest')