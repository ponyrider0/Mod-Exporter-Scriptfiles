{
This Script was designed to automate part of the conversion process to move Tamriel Rebuilt from Morrowind to Morroblivion.
Usage: Within TES4Edit, select the file or records which you want to modify and run the script.  A dialog will ask for a
master file (default is Morrowind_ob.esm).  The script will look at each selected record and compare it to the master file.
If it finds a record in the master file which has the same EditorID or Worldspace X,Y coordinate then it will synchronize
all references to the selected record with the master record and then either renumber the selected record to override the
master record (ie, injection) or alternatively continue using the master record and ignore/delete the selected record.
The alternative is useful for a mod like Tamriel Rebuilt which references records from the master but does not over-ride
them.

Huge thanks to zilav for help with script commands and verbatim use of his GetLandscapeForCell() function.
Parts of code taken from xEdit source code and scripts, especially "Worldspace copy landscapes.pas".
}
unit SyncToMaster;

var
	bDeleteSkipped, bSkipInjection, bRefExactCoords, bRefExactBaseObj, bRefExactBaseClass, bRefMatchLastPass, doOnce: boolean;
	masterFile: IInterface;
	morrowindMasterIndex: integer;
	numDeletedRecords, numRecordsSkipped, numRecordsInTargetFile, numRecordsRenumbered, numTotalRecordsRead, numCellsRead, numMastersFound: integer;
	targetFile: IInterface;


//============================================================================
// returns LAND record for CELL record
//===========================================================================
function GetLandscapeForCell(cell: IInterface): IInterface;
var
  cellchild, r: IInterface;
  i: integer;
begin
  cellchild := FindChildGroup(ChildGroup(cell), 9, cell); // get Temporary group of cell
  for i := 0 to Pred(ElementCount(cellchild)) do begin
    r := ElementByIndex(cellchild, i);
    if Signature(r) = 'LAND' then begin
      Result := r;
      Exit;
    end;
  end;
end;

//============================================================================
// returns PGRD record for CELL record
//===========================================================================
function GetPathgridForCell(cell: IInterface): IInterface;
var
  cellchild, r: IInterface;
  i: integer;
begin
  cellchild := FindChildGroup(ChildGroup(cell), 9, cell); // get Temporary group of cell
  for i := 0 to Pred(ElementCount(cellchild)) do begin
    r := ElementByIndex(cellchild, i);
    if Signature(r) = 'PGRD' then begin
      Result := r;
      Exit;
    end;
  end;
end;

//===========================================================================
// get cell record by X,Y grid coordinates from worldspace
//============================================================================
function GetMasterCellFromXY(Worldspace: IInterface; GridX, GridY: integer): IInterface;
var
	blockidx, subblockidx, cellidx: integer;
	wrldgrup, block, subblock, cell: IInterface;
	Grid, GridBlock, GridSubBlock: TwbGridCell;
	recordID, LabelBlock, LabelSubBlock: Cardinal;
begin
	Grid := wbGridCell(GridX, GridY);
	GridSubBlock := wbSubBlockFromGridCell(Grid);
	LabelSubBlock := wbGridCellToGroupLabel(GridSubBlock);
	GridBlock := wbBlockFromSubBlock(GridSubBlock);
	LabelBlock := wbGridCellToGroupLabel(GridBlock);

	wrldgrup := ChildGroup(Worldspace);
	// iterate over Exterior Blocks
	for blockidx := 0 to Pred(ElementCount(wrldgrup)) do begin
		block := ElementByIndex(wrldgrup, blockidx);
		if GroupLabel(block) <> LabelBlock then Continue;
		// iterate over SubBlocks
		for subblockidx := 0 to Pred(ElementCount(block)) do begin
			subblock := ElementByIndex(block, subblockidx);
			if GroupLabel(subblock) <> LabelSubBlock then Continue;
			// iterate over Cells
			for cellidx := 0 to Pred(ElementCount(subblock)) do begin
				cell := ElementByIndex(subblock, cellidx);
				if (Signature(cell) <> 'CELL') or GetIsPersistent(cell) then Continue;
				if (GetElementNativeValues(cell, 'XCLC\X') = Grid.x) and (GetElementNativeValues(cell, 'XCLC\Y') = Grid.y) then begin
//					if ( CompareText(GetFileName(masterFile), GetFileName(GetFile(cell)))=0  ) then begin
					if (masterFile <> GetFile(cell)) then begin
						addmessage(Format('DEBUG: Warning: found a matching cell but its not in the selected masterFile %s, it is in %s.', [GetFileName(masterFile), GetFileName(GetFile(cell))] ));
						Result := cell;
						Exit;
					end
					else begin
						Result := cell;
						Exit;
					end;
//					if ( GetIsESM(GetFile(cell)) ) then begin
//						Result := cell;
//						Exit;
//					end
//					else begin
//						AddMessage(Format('DEBUG: Warning: found a matching cell for target cell at [%d,%d] but it is not in an ESM (%s)- results will be unexpected.', [GridX, GridY, GetFileName(GetFile(cell))]) );
//						Result := cell;
//						Exit;
//					end;
				end;
			end;
			Break;
		end;
		Break;
	end;
	Result := nil;
end;

//===========================================================================
// get interior cell record by EditorID
//============================================================================
function GetInteriorCellByName(file: IInterface; targetEditorID: string; loadorderTargetID: cardinal): IInterface;
var
	targetReference, masterRecord, cell: IInterface;
	cellGroup, block, subblock: IInterface;
	i, j, k: integer;
	loadorderMasterID: cardinal;
	masterEditorID: string;
begin

	cellGroup := GroupBySignature(file, 'CELL');
	for i := 0 to Pred(ElementCount(cellGroup)) do begin
		block := ElementByIndex(cellGroup, i);
		for j := 0 to Pred(ElementCount(block)) do begin
			subblock := ElementByIndex(block, j);
			for k := 0 to Pred(ElementCount(subblock)) do begin
				cell := ElementByIndex(subblock, k);
				if (Signature(cell) <> 'CELL') then continue;
				masterEditorID := EditorID(cell);
				loadorderMasterID := GetLoadOrderFormID(cell);
//				addmessage( Format('DEBUG: cell(%d) = %s[%s]', [i, masterEditorID, IntToHex(loadorderMasterID, 8)]) );
				if (masterEditorID = targetEditorID) then begin
					if (loadorderMasterID <> loadorderTargetID) then begin
						AddMessage( Format('Interior CELL matched!! %s[%s] == %s[%s]', [targetEditorID, IntToHex(loadorderTargetID, 8), masterEditorID, IntToHex(loadorderMasterID, 8) ]) );
						Result := cell;
						exit;
					end;
				end;
			end;
		end;
	end;

	Result := Nil;	

end;


//===========================================================================
// Use this function to select the master to which to synchronize 
//===========================================================================
procedure FillFilelist(lst:TStrings);
var
	stringlist: TStringList;
	i, j: integer;
	f: IInterface;
	s: string;
begin
	stringlist := TStringList.Create;
	for i := 0 to Pred(FileCount) do begin
		f := FileByIndex(i);
			// If it is the plugin to syncrhonize, then skip
			s := GetFileName(f);
			If (CompareText(s, 'Morrowind_ob.esm')=0) then begin
				morrowindMasterIndex := stringlist.Count;
//				addmessage( Format('DEBUG: %s found at index = %d', [s,morrowindMasterIndex]));
			end;
			stringlist.AddObject(s, f);
	end;
	lst.AddStrings(stringlist);
	stringlist.Free;
end;


//===========================================================================
function OptionsForm: Boolean;
var
	frm: TForm;
	lbl: TLabel;
	cmbFile: TComboBox;
	clbOptions: TCheckListBox;
	btnOk, btnCancel: TButton;
begin
	frm := TForm.Create(nil);
	try
		frm.Caption := 'Synchronize To Master File';
		frm.Width := 326;
		frm.Height := 230;
		frm.Position := poMainFormCenter;
		frm.BorderStyle := bsDialog;
    
		lbl := TLabel.Create(frm);
		lbl.Parent := frm;
		lbl.Left := 8;
		lbl.Top := 8;
		lbl.Caption := 'Using Master:';
    
		cmbFile := TComboBox.Create(frm);
		cmbFile.Parent := frm;
		cmbFile.Left := 8;
		cmbFile.Top := 26;
		cmbFile.Width := 300;
		cmbFile.Style := csDropDownList;
		FillFilelist(cmbFile.Items);
		cmbFile.ItemIndex := morrowindMasterIndex;
		if (cmbFile.ItemIndex = -1) then
			cmbFile.ItemIndex := 0;

		clbOptions := TCheckListBox.Create(frm);
		clbOptions.Parent := frm;
		clbOptions.Top := 60;
		clbOptions.Left := 8;
	        clbOptions.Width := 300;
		clbOptions.Height := 90;
		clbOptions.Items.Add('Skip non-worldspace reference injections');
		clbOptions.Items.Add('Delete skipped injections');
		clbOptions.Items.Add('Require exact coordinate matches');
		clbOptions.Items.Add('Require same base Object for reference matches');
		clbOptions.Items.Add('Require same base Class for reference matches');
		clbOptions.Items.Add('Do last pass for reference matching');
        clbOptions.Checked[0] := false;
        clbOptions.Checked[1] := false;
        clbOptions.Checked[2] := true;
        clbOptions.Checked[3] := true;
        clbOptions.Checked[4] := true;
        clbOptions.Checked[5] := false;
   
		btnOk := TButton.Create(frm);
		btnOk.Parent := frm;
		btnOk.Caption := 'OK';
		btnOk.ModalResult := mrOk;
		btnOk.Left := 150;
		btnOk.Top := clbOptions.Top + clbOptions.Height + 10;
    
		btnCancel := TButton.Create(frm);
		btnCancel.Parent := frm;
		btnCancel.Caption := 'Cancel';
		btnCancel.ModalResult := mrCancel;
		btnCancel.Left := btnOk.Left + btnOk.Width + 10;
		btnCancel.Top := btnOk.Top;
    
		if frm.ShowModal <> mrOk then
			Exit;

		if cmbFile.ItemIndex <> -1 then begin
			masterFile := ObjectToElement(cmbFile.Items.Objects[cmbFile.ItemIndex]);
			bSkipInjection := clbOptions.Checked[0];
			bDeleteSkipped := clbOptions.Checked[1];
            bRefExactCoords := clbOptions.Checked[2];
            bRefExactBaseObj := clbOptions.Checked[3];
            bRefExactBaseClass := clbOptions.Checked[4];
            bRefMatchLastPass := clbOptions.Checked[5];
			Result := True
		end;
  
		finally
		frm.Free;
	end;
end;

//===========================================================================
////////////////////////////////////////////////////////////////////////////
// INITIALIZE
////////////////////////////////////////////////////////////////////////////
//===========================================================================
function Initialize: integer;
begin
	if not wbSimpleRecords then begin
		MessageDlg('Simple records must be checked in xEdit options', mtInformation, [mbOk], 0);
		Result := 1;
		Exit;
	end;
  
  
	if not OptionsForm then begin
		Result := 1;
		Exit;
	end;

	targetFile := nil;
	numDeletedRecords := 0;
	numRecordsRenumbered := 0;
	numCellsRead := 0;
	numMastersFound := 0;
	numTotalRecordsRead := 0;
	numRecordsSkipped := 0;
	numRecordsInTargetFile := 0;
	doOnce := false;
end;

//===========================================================================
// Synchronize Exterior CELL Records (Worldspace records) to master
//===========================================================================
function SynchronizeWorldCell(e: IInterface): integer;
var
	isinterior: boolean;
	targetReference, masterRecord, targetWorld, masterWorld, cell: IInterface;
	data_flags, i, override_count, GridX, GridY: integer;
	newlocalID, loadorderMasterID, loadorderTargetID: cardinal;
	worldName: string;
begin

	Inc(numCellsRead);

	loadorderTargetID := GetLoadOrderFormID(e);
	// First, find the matching worldspace
	targetWorld := LinksTo(ElementByName(e, 'Worldspace'));

	addmessage( Format('DEBUG: Cell: %s is in Worldspace: %s', [ IntToHex(GetLoadOrderFormID(e),8), IntToHex(GetLoadOrderFormID(targetWorld),8)]));

   // Extract name of target, find the corresponding world in master
	worldName := EditorID(targetWorld);
	masterWorld := MainRecordByEditorID( GroupBySignature(masterFile, 'WRLD'), worldName );
	if (Assigned(masterWorld)=0) then begin
//		addmessage( Format('DEBUG: Skipping Cell in Worldspace %s because it was not found in master.', [EditorID(targetWorld)]) );
		// just skip, no need to synchronize
		exit;
	end;

	// If Persistent Cell then skip the X,Y matching function
	if (GetIsPersistent(e)) then begin
		// find the persistent cell in master and over-ride it
		loadorderMasterID := GetLoadOrderFormID(masterWorld)+1;
		while ReferencedByCount(e) > 0 do
			CompareExchangeFormID(ReferencedByIndex(e, 0), loadorderTargetID), loadorderMasterID );
		//  - then renumber override record to masterID
		SetLoadOrderFormID(e, loadorderMasterID );
		//AddMessage ( 'Record renumbered!');
		Inc(numRecordsRenumbered);				
		exit;
	end;

	GridX := GetElementNativeValues(e, 'XCLC\X');
	GridY := GetElementNativeValues(e, 'XCLC\Y');

	// find the matching X,Y cell in masterWorld
	cell := GetMasterCellFromXY(masterWorld, GridX, GridY);
	if (Assigned(cell) ) then begin
		// matching exterior cell found in master, synchronize target and master cells
		loadorderMasterID := GetLoadOrderFormID(cell);
//		AddMessage( Format('DEBUG: [%d,%d] Master LoadFormID: %s to target LoadFormID: %s', [GridX, GridY, IntToHex(loadorderMasterID, 8) , IntToHex(loadorderTargetID, 8)] ) );
		if ( loadorderMasterID <> loadorderTargetID ) then begin // Sanity check
			// Renumber targetID to use master
			//  - find all references to targetID and change to masterID
			while ReferencedByCount(e) > 0 do
				CompareExchangeFormID(ReferencedByIndex(e, 0), loadorderTargetID), loadorderMasterID );
			//  - then renumber override record to masterID
			SetLoadOrderFormID(e, loadorderMasterID );
			//AddMessage ( 'Record renumbered!');
			Inc(numRecordsRenumbered);
		end
		else begin
			// Sanity check is failed, issue error message
//			AddMessage( Format('DEBUG: The target cell %s [%d,%d] already has the same ID as the master record.  Can not synchronize it.', [ IntToHex(loadorderTargetID,8), GridX, GridY]) );
			Inc(numRecordsSkipped);
		end;

		Inc(numMastersFound);

	end 	
	else begin
		// master record was not found, so process the cell as a regular record
		AddMessage( Format('DEBUG: A master record for target cell %s [%d,%d] was not found.', [ IntToHex(loadorderTargetID,8), GridX, GridY]) );
//		SynchronizeOtherRecord(e);
	end;

end;

//===========================================================================
// Synchronize Land Records to master
//===========================================================================
function SynchronizeLandRecord(e: IInterface): integer;
var
	targetReference, masterLand, targetWorld, masterWorld, masterCell, localCell: IInterface;
	data_flags, i, override_count, GridX, GridY: integer;
	newlocalID, loadorderMasterID, loadorderTargetID: cardinal;
	worldName: string;
begin

    localCell := LinksTo(ElementByName(e, 'Cell'));
   // Extract name of target, find the corresponding world in master
	targetWorld := LinksTo(ElementByName(localCell, 'Worldspace'));
	worldName := EditorID(targetWorld);
	masterWorld := MainRecordByEditorID( GroupBySignature(masterFile, 'WRLD'), worldName );
	if (Assigned(masterWorld)=0) then begin
//		addmessage( Format('DEBUG: Skipping LAND in Worldspace %s because it was not found in master.', [EditorID(targetWorld)]) );
		// just skip, no need to synchronize
		Inc(numRecordsSkipped);
		exit;
	end;

	// if equivalent master cell exists, then get the ID for its land record
	// inject e into the master land record's ID
	GridX := GetElementNativeValues(localCell, 'XCLC\X');
	GridY := GetElementNativeValues(localCell, 'XCLC\Y');
	// find the matching cell in masterWorld
	masterCell := GetMasterCellFromXY(masterWorld, GridX, GridY);
    // get LAND record we need to override
    masterLand := GetLandscapeForCell(masterCell);
    // store desired formid and record to renumber later
    if Assigned(masterLand) then begin
		// inject into master File
		loadorderMasterID := GetLoadOrderFormID(masterLand);
		SetLoadOrderFormID(e, loadorderMasterID);
		Inc(numRecordsRenumbered);
	end;

end;

//===========================================================================
// Synchronize PathGrid Records to master
//    Assumes parent Cell has already been matched to a master
//===========================================================================
function SynchronizePathGrid(e: IInterface): integer;
var
	targetReference, masterPathGrid, targetWorld, masterWorld, masterCell, localCell: IInterface;
	data_flags, i, override_count, GridX, GridY: integer;
	newlocalID, loadorderMasterID, loadorderTargetID: cardinal;
	loadorderMasterCELLID, loadorderTargetCELLID: cardinal;
	targetCELLEditorID, masterCELLEditorID: string;
        worldName: string;
begin

    localCell := LinksTo(ElementByName(e, 'Cell'));
    loadorderTargetCELLID := GetLoadOrderFormID(localCell);
    targetCELLEditorID := EditorID(localCell);

//    addmessage( Format('DEBUG: Processing PGRD record: [%s] in %s (%s)', [IntToHex(GetLoadOrderFormID(e), 8), targetCELLEditorID, IntToHex(loadorderTargetCELLID, 8)]) );

    masterCell := MasterOrSelf(localCell);
    masterPathGrid := GetPathgridForCell(masterCell);
    // store desired formid and record to renumber later
    if Assigned(masterPathGrid) then begin
        // inject into master File
        loadorderMasterID := GetLoadOrderFormID(masterPathGrid);
        SetLoadOrderFormID(e, loadorderMasterID);
        Inc(numRecordsRenumbered);
    end
    else begin
        addmessage('masterPathgrid NOT found');
    end;

end;

//===========================================================================
// Synchronize Interior CELL Records to master
//===========================================================================
function SynchronizeInteriorCell(e: IInterface): integer;
var
	isinterior: boolean;
	targetReference, masterRecord, cell: IInterface;
	cellGroup, block, subblock: IInterface;
	i, j, k: integer;
	data_flags, override_count, GridX, GridY: integer;
	newlocalID, loadorderMasterID, loadorderTargetID: cardinal;
	targetEditorID, masterEditorID: string;
begin

	loadorderTargetID := GetLoadOrderFormID(e);
	targetEditorID := EditorID(e);

//	addmessage( 'DEBUG: INTERIOR CELLS');

	cell := GetInteriorCellByName(masterFile, targetEditorID, loadorderTargetID);

	if (Assigned(cell) ) then begin
		// matching exterior cell found in master, synchronize target and master cells
		loadorderMasterID := GetLoadOrderFormID(cell);
		AddMessage( Format('DEBUG: Master LoadFormID: %s to target LoadFormID: %s', [IntToHex(loadorderMasterID, 8) , IntToHex(loadorderTargetID, 8)] ) );
		if ( loadorderMasterID <> loadorderTargetID ) then begin // Sanity check
			// Renumber targetID to use master
			//  - find all references to targetID and change to masterID
			while ReferencedByCount(e) > 0 do
				CompareExchangeFormID(ReferencedByIndex(e, 0), loadorderTargetID), loadorderMasterID );
			//  - then renumber override record to masterID
			SetLoadOrderFormID(e, loadorderMasterID );
			//AddMessage ( 'Record renumbered!');
			Inc(numRecordsRenumbered);
		end
		else begin
			// Sanity check is failed, issue error message
			AddMessage( Format('DEBUG: The target cell %s already has the same ID as the master record.  Can not synchronize it.', [ IntToHex(loadorderTargetID,8)]) );
			Inc(numRecordsSkipped);
		end;
	end 	
	else begin
		// master record was not found, so process the cell as a regular record
		AddMessage( Format('DEBUG: A master record for target cell %s[%s] was not found.', [targetEditorID, IntToHex(loadorderTargetID,8) ]) );
//		SynchronizeOtherRecord(e);
	end;

end;


//===========================================================================
// Find reference XYZ - return object reference that matches position xyz
//===========================================================================
function FindRefByBestMatch(cell, e: IInterface; threshold: double; refMatchRequired, sigMatchRequired, disablePersistent: short): IInterface;
var
	originalRecord, cellChild, r: IInterface;
	i, numMatches, maxMatches, recordType: integer;
	originalRecordID: cardinal;
	originalRecordSignature: string; 
	match, bestMatch, matchRate, lScale, mScale, lX, lY, LZ, lrX, lrY, lrZ, drX, drY, drZ, mrX, mrY, mrZ, dX, dY, dZ, mX, mY, mZ: double;
	matchList: TStringList;
begin
    matchList := TStringList.Create;

    originalRecord := BaseRecord(e);
    originalRecordID := GetLoadOrderFormID(originalRecord);
    originalRecordSignature := Signature(originalRecord);

    lScale := GetElementNativeValues(e, 'XSCL');
    lX := GetElementNativeValues(e, 'DATA\Position\X');
    lY := GetElementNativeValues(e, 'DATA\Position\Y');
    lZ := GetElementNativeValues(e, 'DATA\Position\Z');
    lrX := GetElementNativeValues(e, 'DATA\Rotation\X');
    lrY := GetElementNativeValues(e, 'DATA\Rotation\Y');
    lrZ := GetElementNativeValues(e, 'DATA\Rotation\Z');

    if (GetIsPersistent(e)<>0) then begin
        recordType := 8;
    end
    else begin
        recordType := 9;
    end;
    if (disablePersistent <> 0) then recordType := 9;
    cellChild := FindChildGroup(ChildGroup(cell), recordType, cell);
    if (Assigned(cellChild)=0) then begin
        addmessage( Format( 'ERROR: FindRefByBestMatch() Could NOT find a cell in ChildGroup for cell %s. How did this happen? Dont know.', [IntToHex(GetLoadOrderFormID(cell),8)]) );
    exit;
    end;
    for i := 0 to Pred(ElementCount(cellchild)) do begin
        r := ElementByIndex(cellchild, i);
        if (OverrideCount(r) > 0) then continue;
        if (Signature(r) = 'PGRD') then continue;
        // get positions
        mScale := GetElementNativeValues(r, 'XSCL');
        mX := GetElementNativeValues(r, 'DATA\Position\X');
        mY := GetElementNativeValues(r, 'DATA\Position\Y');
        mZ := GetElementNativeValues(r, 'DATA\Position\Z');
        mrX := GetElementNativeValues(r, 'DATA\Rotation\X');
        mrY := GetElementNativeValues(r, 'DATA\Rotation\Y');
        mrZ := GetElementNativeValues(r, 'DATA\Rotation\Z');
		
        dX := abs(mX - lX);
        // if (dX < 0) then dX := -1*dX;
        dY := abs(mY - lY);
        //if (dY < 0) then dY := -1*dY;
        dZ := abs(mZ - lZ);
        //if (dZ < 0) then dZ := -1*dZ;

        drX := abs(mrX - lrX);
        //if (drX < 0) then drX := -1*drX;
        drY := abs(mrY - lrY);
        //if (drY < 0) then drY := -1*drY;
        drZ := abs(mrZ - lrZ);
        //if (drZ < 0) then drZ := -1*drZ;

        numMatches := 0;
        maxMatches := 0;
        if (originalRecordID = GetLoadOrderFormID(BaseRecord(r)) ) then begin
            numMatches := numMatches+20;
            maxMatches := maxMatches+20;
        end
        else if (refMatchRequired = 0) and (originalRecordSignature = Signature(BaseRecord(r)) ) then begin
            numMatches := numMatches+10;
            maxMatches := maxMatches+10;
        end
        else if (refMatchRequired <> 0) or (sigMatchRequired <> 0) then begin
            continue;
        end
        else if (bRefExactCoords = 0) then begin
            numMatches := numMatches+0;
            maxMatches := maxMatches+10;
        end;
        if (mScale = 0) and (lScale = 0) then begin
            numMatches := numMatches+0;
        end
        else begin
            if (mScale = 0) then mScale := 1;
            if (lScale = 0) then lScale := 1;
            if (abs(mScale-lScale) < 0.10) then begin
//              AddMessage (Format('Scale match was found: mScale(%4f)-lScale(%4f)=dScale(%4f) < 0.10.', [mScale, lScale, abs(mScale-lScale)]) );
                numMatches := numMatches+3;
                maxMatches := maxMatches+3;
            end
            else if (abs(mScale-lScale) < 0.50) then begin
//              AddMessage (Format('Scale match was found: mScale(%4f)-lScale(%4f)=dScale(%4f) < 0.50.', [mScale, lScale, abs(mScale-lScale)]) );
                numMatches := numMatches+1;
                maxMatches := maxMatches+3;
            end;
        end;
        if (dx < 1) then begin
            numMatches := numMatches+20;
            maxMatches := maxMatches+20;
        end
        else if (dx < threshold) then begin
            numMatches := numMatches+18;
            maxMatches := maxMatches+20;
        end
        else if (dx < threshold*10) then begin
            numMatches := numMatches+16;
            maxMatches := maxMatches+20;
        end
        else if (dx < threshold*100) then begin
            numMatches := numMatches+15;
            maxMatches := maxMatches+20;
        end
        else begin
            numMatches := numMatches+0;
            maxMatches := maxMatches+20;
        end;
        if (dy < 1) then begin
            numMatches := numMatches+20;
            maxMatches := maxMatches+20;
            end
        else if (dy < threshold) then begin
            numMatches := numMatches+18;
            maxMatches := maxMatches+20;
        end
        else if (dy < threshold*10) then begin
            numMatches := numMatches+16;
            maxMatches := maxMatches+20;
        end
	else if (dy < threshold*100) then begin
	    numMatches := numMatches+15;
    	    maxMatches := maxMatches+20;
    	end
        else begin
	    numMatches := numMatches+0;
            maxMatches := maxMatches+20;
	end;			
	if (dz < 1) then begin
            numMatches := numMatches+20;
            maxMatches := maxMatches+20;
	end
	else if (dz < threshold) then begin
            numMatches := numMatches+18;
            maxMatches := maxMatches+20;
	end
	else if (dz < threshold*10) then begin
            numMatches := numMatches+16;			
            maxMatches := maxMatches+20;
        end
        else if (dz < threshold*100) then begin
            numMatches := numMatches+15;
            maxMatches := maxMatches+20;
    	end
        else begin
            numMatches := numMatches+0;
            maxMatches := maxMatches+20;
        end;
        // no points for rotation if rx=0
        if (mrx = 0) and (lrx = 0) then begin
            numMatches := numMatches+0;
        end
	else if (drx < 1) then begin
            numMatches := numMatches+10;
            maxMatches := maxMatches+10;
        end
        else if (drx < threshold) then begin
            numMatches := numMatches+9;
            maxMatches := maxMatches+10;
        end
        else if (drx < threshold*10) then begin
            numMatches := numMatches+1;
            maxMatches := maxMatches+2;
        end
        else begin
            numMatches := numMatches+0;
            maxMatches := maxMatches+2;
        end;
        if (mry = 0) and (lry = 0) then begin
//          numMatches := numMatches+0;
        end
        else if (dry < 1) then begin
            numMatches := numMatches+10;
            maxMatches := maxMatches+10;
        end
        else if (dry < threshold) then begin
            numMatches := numMatches+9;
            maxMatches := maxMatches+10;
        end
        else if (dry < threshold*10) then begin
            numMatches := numMatches+1;
            maxMatches := maxMatches+2;
        end
        else begin
            numMatches := numMatches+0;
            maxMatches := maxMatches+2;
        end;
        if (mrz = 0) and (lrz = 0) then begin
//          numMatches := numMatches+0;
      	end
        else if (drz < 1) then begin
            numMatches := numMatches+10;
            maxMatches := maxMatches+10;
        end
        else if (drz < threshold) then begin
            numMatches := numMatches+9;
            maxMatches := maxMatches+10;
        end
        else if (drz < threshold*10) then begin
            numMatches := numMatches+1;
            maxMatches := maxMatches+2;
        end
        else begin
            numMatches := numMatches+0;
            maxMatches := maxMatches+2;
        end;
        if (maxMatches <> 0) then begin
            matchRate := numMatches / maxMatches
        end
        else begin
            matchRate := 0;
        end;

//	if (dX < threshold) and (dY < threshold) and (dZ < threshold) and (drX < threshold) and (drY < threshold) and (drZ < threshold) then begin
//	    addmessage(Format('DEBUG: found a match! master(%4f, %4f, %4f) = target(%4f, %4f, %4f)', [mX, mY, mZ, lX, lY, lZ]));
        if (matchRate = 1.0) then begin
//          Result := r;
	    if (true) then begin
             // return nil to skip injection, then delete exact match
                addmessage(Format('DEBUG: exact match found: [ %s ] = [ %s ]', [IntToHex(GetLoadOrderFormID(e),8), IntToHex(GetLoadOrderFormID(r),8)]));
                Result := r;
                matchlist.free;
                exit;
            end
            else begin
                // return nil to skip injection, then delete exact match
                addmessage(Format('DEBUG: exact match found: [ %s ] = [ %s ], deleting...', [IntToHex(GetLoadOrderFormID(e),8), IntToHex(GetLoadOrderFormID(r),8)]));
                Result := nil;
                Inc(numDeletedRecords);
                Remove(e);
            end;
            matchList.free;
            exit;
        end
        else if (threshold > 1) then begin
            if (matchRate > 0.4) then begin
//              addmessage(Format('DEBUG: recording near match: %s has matchrate:%4f', [IntToHex(FormID(r), 8), matchRate]));
                matchList.Add( Format('$%s=%4f', [IntToHex(FormID(r),8), matchRate]) );
            end
            else begin
//              addmessage(Format('DEBUG: record (%s) was not a match -- matchscore was %f4, continuing...', [IntToHex(FormID(r),8), matchRate]));
            end;
        end;
	end;

    // finished list of children but no exact match, now find the closest match
    if matchList.Count = 0 then begin
        addmessage(Format('DEBUG: No matches found after processing %d records from masterCell %s for [ %s ]', [i, IntToHex(FormID(cell),8), IntToHex(GetLoadOrderFormID(e),8)]));
        matchlist.free;
        if ((GetIsPersistent(e) <> 0) and (disablePersistent = 0)) then begin
            Result := FindRefByBestMatch(cell, e, threshold, refMatchRequired, sigMatchRequired, true);
        end;
        exit;
    end;
    bestMatch := 0;
    for i := 0 to matchList.count-1 do begin
        match := matchList.ValueFromIndex[i];
//      addmessage(Format('DEBUG: looking for nearest match, index %d: "%s" = %4f', [i, matchList.Names[i], match]));
        if (match > bestMatch) then begin
            bestMatch := match;
            Result := RecordByFormID(masterFile, StrToInt64(matchList.Names[i]),0);
        end
    end;
    if (((bRefMatchLastPass = 0) and (bestMatch < 0.8)) or ((bRefMatchLastPass <> 0) and (bestMatch < 0.6))) then begin
        addmessage(Format('DEBUG: No acceptable match found for [ %s ]. Closest match was only [ %s ] = %4f out of %d matches.', [IntToHex(GetLoadOrderFormID(e),8), IntToHex(GetLoadOrderFormID(Result),8), bestMatch, matchList.count]));
        Result := nil;
       	if ((GetIsPersistent(e) <> 0) and (disablePersistent = 0)) then begin
       	    Result := FindRefByBestMatch(cell, e, threshold, refMatchRequired, sigMatchRequired, true);
        end;
    end
    else begin
        addmessage(Format('DEBUG: Exact match not found for [ %s ]. Best match selected is [ %s ] = %4f out of %d matches', [IntToHex(GetLoadOrderFormID(e),8), IntToHex(GetLoadOrderFormID(Result),8), bestMatch, matchList.count]));
    end;

    matchList.free;

end;


//===========================================================================
// Synchronize PlacedObject References with Master
//===========================================================================
function SynchronizePlacedObject(e: IInterface): integer;
var
	masterReference, originalRecord, targetWorld, masterWorld, masterCell, targetCell: IInterface;
	targetOffset, masterOffset: cardinal;
	newlocalID, loadorderMasterID, loadorderTargetID: cardinal;
	baseRecordSignature, baseRecordEditorID, worldName, targetEditorID: string;
	GridX, GridY, offset, i, threshold: integer;
	lrX, lrY, lrZ, lX, lY, lZ: double;
//	targetPos: TwbVector;
begin

	// change the next line to "if (false) then begin" to enable this function
	// you must configure options programmatically through function arguments to FindRefByBestMatch() -- see below
	if (false) then begin
		Inc(numRecordsSkipped);
		exit;
	end;

	// Draft Pseudocode:
	// 1. get XYZ data, get base record EditorID
	// 2. get local parent CELL and match to master parent CELL
	// 3. get children of master parent CELL
	// 4. foreach master child, compare XYZ to e.  If within threshold then...
	// 5.		if toggleEditorIDMatch: check for editorID match, if not then skip
	// 6.		else inject into master
	// 7.TODO:			if toggleOverridePositionOnly, copy master to new record then overwrite with local XYZ
	// 8.			else if toggleOverrideAll, inject local record into master ID

// TODO: uncomment when working
//	if (OverrideCount(MasterOrSelf(e))>0) then begin
//		Inc(numRecordsSkipped);
//		exit;
//	end;

	loadorderTargetID := GetLoadOrderFormID(e);
	targetEditorID := EditorID(e);

	originalRecord := BaseRecord(e);
	baseRecordEditorID := EditorID(originalRecord);
	baseRecordSignature := Signature(originalRecord);

	// TODO: must change this code so that it loads the primary master cell from the primary master file rather than the cell from a previous over-ride file
    targetCell := LinksTo(ElementByName(e, 'Cell'));
	// Check to see if this is cell has already been injected into the masterFile
	masterCell := MasterOrSelf(targetCell);
	// debug line, remove when working...
//	addmessage( format('DEBUG2: masterFile= %s, masterCell = %s, targetrecord = %s ', [GetFileName(masterFile), GetFileName(GetFile(masterCell)), IntToHex(GetLoadOrderFormID(e),8)]));
//	if ( CompareText(GetFileName(masterFile),GetFileName(GetFile(masterCell))) <> 0 ) then begin
	if (masterFile <> GetFile(masterCell)) then begin
		// targetCell has not yet been injected, so do more work to retrieve the appropriate masterCell
//		addmessage(Format('DEBUG: targetCell %s has not yet been injected into master, so we need to retrieve the equivalent cell in the master so that we can search the records within the masterCell', [IntToHex(GetLoadOrderFormID(targetCell),8)]));
		targetWorld := LinksTo(ElementByName(targetCell,'Worldspace'));
		worldName := EditorID(targetWorld);
		masterWorld := MainRecordByEditorID( GroupBySignature(masterFile, 'WRLD'), worldName );
		if (Assigned(masterWorld)=0) then begin
			// just skip, no need to synchronize
			Inc(numRecordsSkipped);
			exit;
		end;
		// find the matching cell in masterWorld
		// first, check if this is the worldspace persistent cell so that we can retrieve the master in a different way
		if (GetIsPersistent(targetCell)=true) then begin
			addmessage(Format('DEBUG: targetCell %s is persistent', [IntToHex(GetLoadOrderFormID(targetCell),8)]));
//			masterCell := RecordByFormID(GetFile(masterCell), FormID(masterWorld)+1, true);
			masterCell := RecordByFormID(masterFile, FormID(masterWorld)+1, true);
			addmessage(Format('DEBUG: masterCell %s is retrieved from masterFile %s', [IntToHex(GetLoadOrderFormID(masterCell), 8), GetFileName(GetFile(masterCell))]));
		end
		else begin
			GridX := GetElementNativeValues(targetCell, 'XCLC\X');
			GridY := GetElementNativeValues(targetCell, 'XCLC\Y');
			masterCell := GetMasterCellFromXY(masterWorld, GridX, GridY);
		end;
	end
	else begin
//		addmessage(Format('DEBUG: great, the targetCell %s is already injected into the master, so we can proceed to searching for an equivalent master record', [IntToHex(GetLoadOrderFormID(targetCell),8)]));
	end;

	// call function to search for a bestmatch to target record. 
	// syntax for function is FindRefByBestMatch(masterCell, targetRecord, CoordinateThreshold, bMustMatchBaseEditorID, bMustMatchBaseSignature)
    	if (bRefExactCoords <> 0) then begin
        	threshold := 1;
    	end
    	else begin
        	threshold := 3;
    	end;
	masterReference := FindRefByBestMatch(masterCell, e, threshold, bRefExactBaseObj, bRefExactBaseClass, false);
	if (Assigned(masterReference) = 0) then begin
		// no match found, skip
//		addmessage (Format('DEBUG: No match found for ref: %s', [IntToHex(loadorderTargetID,8)]));
		Inc(numRecordsSkipped);
		exit;
	end;
	loadorderMasterID := GetLoadOrderFormID(masterReference);

	// override masterReference
	if (loadorderMasterID <> loadorderTargetID) then begin
//		if (Assigned(RecordByFormID(targetFile,LoadOrderFormIDtoFileFormID(targetFile,loadOrderMasterID),1))=0) then begin
		if (OverrideCount(masterReference) = 0) then begin
			SetLoadOrderFormID(e, loadorderMasterID);
			Inc(numRecordsRenumbered);
		end
		else begin
			addmessage(Format('ERROR: record %s is already overrided (%d times). Conflict Loser is %s', [IntToHex(loadorderMasterID,8), OverrideCount(masterReference), IntToHex(loadorderTargetID,8)]));
		end;
	end
	else begin
		Inc(numRecordsSkipped);
		exit;
	end;

//	addmessage( Format('DEBUG: Object overrided: [%s] base:%s at %f, %f, %f', [IntToHex(loadorderTargetID, 8), baseRecordEditorID, lX, lY, lZ]) );

end;


//===========================================================================
// Synchronize Other Records to master
//===========================================================================
function SynchronizeOtherRecord(e: IInterface): integer;
var
	masterRecord: IInterface;
	targetOffset, masterOffset: cardinal;
	newlocalID, loadorderMasterID, loadorderTargetID: cardinal;
	targetSignature, targetEditorID: string;
	offset, i: integer;
begin

	// get ID of e, see if it exists in master -- if so compare their signatures and then editorids
	loadorderTargetID := GetLoadOrderFormID(e);
	targetEditorID := EditorID(e);
	targetSignature := Signature(e);
	// DEBUG message: output localID of record
	addmessage( Format('DEBUG: Processing other record: [%s] %s (%s)', [IntToHex(loadorderTargetID, 8), targetEditorID, targetSignature]) );

	// Look for an equivalent record in the master file, if it exists, then synchronize with it (i.e., inject into master as override record)
	masterRecord := MainRecordByEditorID( GroupBySignature(masterFile, targetSignature), targetEditorID );
	if (Assigned(masterRecord) <> 0) then begin
		// equivalent master record found... check IDs, then synchronize
		loadorderMasterID := GetLoadOrderFormID(masterRecord);
		if (loadorderMasterID <> loadorderTargetID) then begin // This is just a sanity check before proceeding
			// synchronize
			addmessage( Format('DEBUG: record: "%s"[%s] (%s) <> master: "%s"[%s]', [targetEditorID, IntToHex(loadOrdertargetID,8), targetSignature, EditorID(masterRecord), IntToHex(loadorderMasterID,8) ]) );

			// Prepare to inject target record and all renumber all references into master File as an override to master record
			//  - find all references to targetID and change to masterID, this assumes that e is not an override record 
			while ReferencedByCount(e) > 0 do
				// move all references in the target to point to the master record instead of the target record
				CompareExchangeFormID(ReferencedByIndex(e, 0), loadorderTargetID, loadorderMasterID );
			//  Now renumber the target ID to the master ID so that it will be injected into the masterFile as an override
			if (bSkipInjection) and (targetSignature <> 'WRLD') and (targetSignature <> 'CELL') and (targetSignature <> 'LAND') then begin
				// skip injection but still keep the renumbered references above
				if (bDeleteSkipped) then begin
					RemoveNode(e);
					Inc(numDeletedRecords);
//					AddMessage(Format('Record %s[%s]deleted.', [EditorID(e), IntToHex(loadorderTargetID,8)]) );
				end;
				Inc(numRecordsSkipped);
			end	
			else begin
				// renumber(ie, inject) e into the master File
				SetLoadOrderFormID(e, loadorderMasterID);
			end;
			//AddMessage ( 'Record renumbered!');
			Inc(numRecordsRenumbered);

		end
		else begin
			// you shouldn't be here, the target and master IDs are already the same, something went wrong
			addmessage( Format('ERROR: The target %s[%s] already has the same ID as the master record.  Can not synchronize it.', [EditorID(e), IntToHex(loadorderTargetID,8)]) );
			Inc(numRecordsSkipped);
		end;

	end 	
	else begin
		addmessage( Format('No matching master record found for %s[%s].', [EditorID(e), IntToHex(loadorderTargetID,8)]) );
		// An equivalent master record was not found, do not inject into master file
		// No need to do any further processing

	end;

end;


//===========================================================================
function Process(e: IInterface): integer;
var
	cell, group: IInterface;
//	isinterior: boolean;
	percentComplete: single;
	data_flags: integer;
begin

    if (IsMaster(e) = 0) then begin
//        AddMessage( Format('Skipping WinningOverride Record: %s.', [IntToHex(GetLoadOrderFormID(e),8)]) );
        exit;
    end;

	if (targetFile <> GetFile(e)) then begin
		targetFile := GetFile(e);
		numRecordsInTargetFile := numRecordsInTargetFile + RecordCount(targetFile);
	end;

	// Check to see if file is already linked to a master, if so then show message and exit
	if (doOnce = false) then begin
		doOnce := true;
		// Add Selected Master if not already done
		if (HasMaster(targetFile, GetFileName(masterFile))) then begin
			// target file already linked to selected master, this script assumes they start unlinked...
			// Issue warning
			AddMessage( Format('WARNING: file %s is already linked to master %s.', [GetFileName(targetFile), GetFileName(masterFile)]) );
		end
		else begin
			AddMessage( Format('Adding %s as a Master to target %s, Please wait...', [GetFileName(masterFile), GetFileName(targetFile)]) );
			AddMasterIfMissing(targetFile, GetFileName(masterFile));
			AddMessage( 'Add Master Complete. Continuing script...');
		end;
	end;
	
	// If cell exterior type, then prepare perform XY link
	// If not exterior cell type, then perform standard record Synch

	if Signature(e) = 'CELL' then begin
//		addmessage( 'DEBUG: CELLS');
		data_flags := GetElementNativeValues(e, 'DATA');
		// check if it is an exterior cell, if so, use worldcell
		if (data_flags and 1) = 0 then begin // This checks to see if the flag IsInterior=0
			// process exterior cells
			SynchronizeWorldCell(e);
		end
		else begin
			// process interior cells (IsInterior = 1)
			SynchronizeInteriorCell(e);
		end;
	end
	else if Signature(e) = 'LAND' then begin
		// process land record
//		addmessage( 'DEBUG: LAND');
		SynchronizeLandRecord(e);
	end
    else if Signature(e) = 'PGRD' then begin
        SynchronizePathGrid(e);
    end
	else if (Signature(e) = 'REFR') or (Signature(e) = 'ACHR') or (Signature(e) = 'ACRE') then begin
//		addmessage( 'DEBUG: REFR');
		SynchronizePlacedObject(e);
	end
	else begin
//		addmessage( 'DEBUG: other');
		// Process non-CELL records
		SynchronizeOtherRecord(e);
	end;

	// Do statistics tracking and update messages

	Inc(numTotalRecordsRead);

	if (numTotalRecordsRead mod 100000 = 0) and (numTotalRecordsRead > 0) then begin
		if (numRecordsInTargetFile = 0) then
			numRecordsInTargetFile := RecordCount(targetFile);
		percentComplete := (numTotalRecordsRead / numRecordsInTargetFile) * 100;
		AddMessage( Format('%4f percent of records in target file read (%d of %d total records): %d exterior cells found with %d matched to master, %d other records found. %d records renumbered. %d records skipped (%d deleted).', [percentComplete, numTotalRecordsRead, numRecordsInTargetFile, numCellsRead, numMastersFound, (numTotalRecordsRead-numCellsRead), numRecordsRenumbered, numRecordsSkipped, numDeletedRecords]) );
	end;

end;

//===========================================================================
function Finalize: integer;
begin
	AddMessage( Format('Script Completed. Total stats: %d records read, %d exterior cells, %d other records, %d records renumbered, %d records skipped (%d deleted).', [numTotalRecordsRead, numCellsRead, numTotalRecordsRead-numCellsRead, numRecordsRenumbered, numRecordsSkipped, numDeletedRecords]) );

end;

end.
