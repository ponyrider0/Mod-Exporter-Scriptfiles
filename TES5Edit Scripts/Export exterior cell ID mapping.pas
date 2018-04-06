{
  Export mapping of CELL X,Y to FormID
}
unit UserScript;

var
  stringbuffer: TStringList;




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


//================================================
// Process
//================================================
function Process(e: IInterface): integer;
var
    land, pathgrid: IInterface;
    cellInfo, cellName: string;
    cellX, cellY, data_flags: integer;
    cellFormID, landFormID, pathgridID: cardinal;
begin

  if Signature(e) <> 'CELL' then
    Exit;

  data_flags := GetElementNativeValues(e, 'DATA');
  if (data_flags and 1) = 1 then // This checks to see if the flag IsInterior=0
    // process exterior cells
    Exit;

  if (GetIsPersistent(e)) then
    exit;

  cellFormID := GetLoadOrderFormID(e);
  land := GetLandscapeForCell(e);
  landFormID := GetLoadOrderFormID(land);
  pathgrid := GetPathgridForCell(e);
  pathgridID := GetLoadOrderFormID(pathgrid);

  cellX := GetElementNativeValues(e, 'XCLC\X');
  cellY := GetElementNativeValues(e, 'XCLC\Y');

  cellName := GetElementEditValues(e, 'EDID');
  if cellName = '' then
    cellName := 'wilderness';

  cellInfo := Format('0x%s,%d,%d,"%s",0x%s,0x%s', [IntToHex(cellFormID, 8), cellX, cellY, cellName, IntToHex(landFormID,8), IntToHex(pathgridID,8)]);
  stringbuffer.Add(cellInfo);

end;

//================================================
// Initialize
//================================================
function Initialize: integer;
var
    header: string;
begin
  stringbuffer:= TStringList.Create;
  header := 'FormID,GridX,GridY,EDID,LandscapeID,PathgridID';
  stringbuffer.Add(header);
end;

//================================================
// Finalize
//================================================
function Finalize: integer;
var
  fname: string;
begin
  fname := ProgramPath + 'cellmapping.csv';
  AddMessage('Saving list to ' + fname);
  stringbuffer.SaveToFile(fname);
  stringbuffer.Free;
end;

end.
