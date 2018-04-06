{
  Export mapping of CELL X,Y to FormID
}
unit UserScript;

var
  stringbuffer: TStringList;
  modFileName: string;

//================================================
// Process
//================================================
function Process(e: IInterface): integer;
var
    recordInfo, editorID, fullName, sSIG: string;
    formID: cardinal;
begin

  formID := GetLoadOrderFormID(e);
  editorID := GetElementEditValues(e, 'EDID');
  fullName := GetElementEditValues(e, 'FULL');
  sSIG := Signature(e);

  if modFileName = '' then
    modFileName := GetFileName(GetFile(e));

  if editorID = '' then
    exit;

  recordInfo := Format('%s,,"%s",,0x%s,"%s"', [ sSIG, editorID, IntToHex(formID, 8), fullName]);
  stringbuffer.Add(recordInfo);

end;

//================================================
// Initialize
//================================================
function Initialize: integer;
var header: string;
begin
  stringbuffer:= TStringList.Create;
  header := 'RecordType,ModFilename,EDID,NumReferences,FormID,Fullname';
  stringbuffer.Add(header);
end;

//================================================
// Finalize
//================================================
function Finalize: integer;
var
  fname: string;
begin
  fname := ProgramPath + '\' + modFileName + '_FormIDlist.csv';
  AddMessage('Saving list to ' + fname);
  stringbuffer.SaveToFile(fname);
  stringbuffer.Free;
end;

end.
