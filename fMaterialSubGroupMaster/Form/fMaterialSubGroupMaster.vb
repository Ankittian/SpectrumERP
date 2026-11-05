Imports BaseArchitecture.BusinessLogicLayer.ClsCommonFunction
Imports Infragistics.Win.UltraWinGrid

Public Class fMaterialSubGroupMaster
    Implements IMDIFunctions

    Dim bIsLoading As Boolean
    Dim bIsReset As Boolean
    Dim strError As String
    Dim WithEvents aCheckBoxOnBinHeader_CreationFilter As New ClsCheckBoxOnHeader(True)

    Private Sub ImportSheet()
        Try
            Dim objclsReadExcelFile As New clsReadExcelFile
            Dim dt As DataTable = objclsReadExcelFile.GetExcelSheetDetail

            If clsReadExcelFile.strFilePath <> "" Then

                objBase.RefreshForm(ugdFastEntry)

                objclsReadExcelFile.strColumnNames = New String() {"Category Name", "Group Name", "Code", "Sub Group Name"}

                Dim dtImported As DataTable = objclsReadExcelFile.GetSheetTable(Convert.ToString(Me.Tag) & "$")

                dtImported.Columns.Add("Remarks")
                dtImported.AcceptChanges()

                objBase.GrdSetDataSource(ugdFastEntry, dtImported)

            End If

        Catch ex As Exception
            Throw ex
        End Try

    End Sub

    Public Sub NewRecord() Implements IMDIFunctions.NewRecord
        Try
            Dim frm As mdiProject = CType(Me.MdiParent, mdiProject)
            frm.NewRecord()

        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try
    End Sub

    Private Sub Form_Load(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles MyBase.Load
        Try
            Dim listOfCombos As Control() = New Control() {ucmbCategoryName, ucmbGroupName, utxtCode, utxtSubGroupName}
            objBase.CompulsaryField(listOfCombos)

            bIsLoading = True
            bIsReset = True

            ufllSubGroupCode.Value = "<a title=""Switch to fast entry mode."">Sub Group Code</a>"
            ufllSubGroupCode.ShowTitleToolTips = True

            ufllSubGroupCode.Height = 20
            ufllBackFastEntry.Height = 20

        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try
    End Sub

    Private Function ValidateForm() As Boolean
        Try
            ugdDivisionDetail.UpdateData()
            ugdMakeDetail.UpdateData()
            ugdUOM.UpdateData()
            ugdVendorDetail.UpdateData()

            ugdFastEntry.UpdateData()
            strError = Nothing

            Dim objDTMaterialSubGroupMaster As New DataLayer.DTMaterialSubGroupMaster()
            objDTMaterialSubGroupMaster.GroupNo = CType(ucmbGroupName.Value, Nullable(Of Short))
            objDTMaterialSubGroupMaster.SubGroupName = utxtSubGroupName.Text.Trim
            objDTMaterialSubGroupMaster.CompanyNo = gCompanyNo
            objDTMaterialSubGroupMaster.FullSubGroupCode = utxtSubgroupCode.Text.Trim

            If objLocalBase.getId() Is Nothing Then
                objDTMaterialSubGroupMaster.SubGroupNo = Nothing
            Else
                objDTMaterialSubGroupMaster.SubGroupNo = Convert.ToInt16(objLocalBase.getId())
            End If

            Dim ds As DataSet = objDTMaterialSubGroupMaster.Validate()

            Dim dr As DataTableReader = ds.Tables(0).CreateDataReader()

            If dr.Read() Then
                If Convert.ToString(dr(0)) = "0" Then

                    If ugbFastEntry.Visible = False Then
                        objBase.ErrorMessage(Convert.ToString(dr(1)))
                    Else
                        strError = Convert.ToString(dr(1))
                    End If

                    Return False
                End If
            End If
            dr.Close()

            If ucmbCategoryName.SelectedRow Is Nothing Then

                If ugbFastEntry.Visible = False Then
                    objBase.ValidationMessage("Select valid Category Name.")
                    ucmbCategoryName.Focus()
                Else
                    strError = "Select valid Category Name."
                End If

                Return False
            End If

            If ucmbGroupName.SelectedRow Is Nothing Then

                If ugbFastEntry.Visible = False Then
                    objBase.ValidationMessage("Select valid Group Name.")
                    ucmbGroupName.Focus()
                Else
                    strError = "Select valid Group Name."
                End If

                Return False
            End If

            If utxtCode.Text.Trim = "" Then
                objBase.ValidationMessage("Enter Code.")
                utxtCode.Focus()
                Return False
            End If

            If utxtSubGroupName.Text.Trim = "" Then

                If ugbFastEntry.Visible = False Then
                    objBase.ValidationMessage("Enter Sub Group Name.")
                    utxtSubGroupName.Focus()
                Else
                    strError = "Enter Sub Group Name."
                End If

                Return False
            End If


            If uQcGroup.ValidateForm(utabMain.Tabs("QC")) = False Then
                Return False
            End If

            'Dim dtDiv As DataTable = ugdDivisionDetail.DataSource
            'If dtDiv.Select("[Select]='True'").Length = 0 Then
            '    objBase.Validate(ugdDivisionDetail.Rows(0).Cells("Select"), "Select atleast one Warehouse.", utabMain.Tabs("DD"))
            '    Exit Function
            'End If

            For Each row As UltraGridRow In ugdVendorDetail.Rows
                If Convert.ToString(row.Cells("Vendor Name").Value) <> "" Then

                    If Convert.ToString(row.Cells("Location").Value) = "" Then
                        objBase.Validate(row.Cells("Location"), "Select valid Location", utabMain.Tabs("VD"))
                        Return False
                    End If

                End If
            Next

            ValidateForm = True
        Catch ex As Exception
            Throw ex
        End Try
    End Function

    Public Sub LoadData(ByVal optionalValue As Object) Implements IMDIFunctions.LoadData
        Try
            Reset()
            FillValues()
            Dim objDTMaterialSubGroupMaster As New DataLayer.DTMaterialSubGroupMaster

            objDTMaterialSubGroupMaster.SubGroupNo = Convert.ToInt16(objLocalBase.getId())
            objDTMaterialSubGroupMaster.CompanyNo = gCompanyNo

            Dim ds As DataSet = objDTMaterialSubGroupMaster.LoadData()

            Dim dr As DataTableReader = ds.Tables(4).CreateDataReader()

            If dr.Read() Then
                objBase.ControlValueFromProcedure(ucmbCategoryName, dr("CategoryNo"))
                objBase.ControlValueFromProcedure(ucmbGroupName, dr("GroupNo"))

                objBase.ControlValueFromProcedure(utxtCode, dr("Code"))
                objBase.ControlValueFromProcedure(utxtSubGroupName, dr("SubGroupName"))

                objBase.ControlValueFromProcedure(utxtReceiptTolerance, dr("ReceiptTolerance"))
                objBase.ControlValueFromProcedure(utxtShipmentTolerance, dr("ShipmentTolerance"))

                objBase.ControlValueFromProcedure(uchkInActive, dr("InActive"))
                objBase.ControlValueFromProcedure(ucmbGSTCategory, dr("GSTCategoryNo"))

                objBase.ControlValueFromProcedure(ucmbHSNSACCode, dr("HSNSACCodeNo"))
                objBase.ControlValueFromProcedure(uchkBINApplicable, dr("IsBinApplicable"))

                objBase.ControlValueFromProcedure(utxtDispatchNegTolerance, dr("DispatchNegTolerance"))
            End If
            dr.Close()

            objBase.GrdSetDataSource(ugdMakeDetail, ds.Tables(0))

            objBase.GrdSetDataSource(ugdUOM, ds.Tables(2))

            objBase.GrdSetDataSource(ugdVendorDetail, ds.Tables(3))
            uQcGroup.GridDataSource = ds.Tables(1)

            If gHeadOfficeNo <> gCompanyNo Then
                objBase.LockEachControl(Me)
                uchkInActive.Enabled = False
            End If
            ugdBinDetail.DisplayLayout.Bands(0).Override.AllowUpdate = Infragistics.Win.DefaultableBoolean.True
        Catch ex As Exception
            Throw ex
        End Try
    End Sub

    Public Function Delete() As Boolean Implements IMDIFunctions.Delete
        Dim functionReturnValue As Boolean = False
        Try

            If objLocalBase.getId() Is Nothing Then
                Return False
            End If

            If gHeadOfficeNo <> gCompanyNo Then
                objBase.FormValidation("Permission denied to delete Material Sub Group.")
                Return False
            End If
            If objBase.DeleteMessage() = False Then

                Dim objDTMaterialSubGroupMaster As New DataLayer.DTMaterialSubGroupMaster

                objDTMaterialSubGroupMaster.SubGroupNo = Convert.ToInt16(objLocalBase.getId())

                Dim ds As DataSet = objDTMaterialSubGroupMaster.Delete()

                Dim dr As DataTableReader = ds.Tables(0).CreateDataReader()

                If dr.Read() Then
                    If Convert.ToString(dr(0)) = "0" Then
                        objBase.DeleteValidationMessage(Convert.ToString(dr(1)))
                    ElseIf Convert.ToString(dr(0)) = "1" Then
                        objBase.DeleteSuccessMessage()
                        functionReturnValue = True
                        NewRecord()
                    End If
                End If
                dr.Close()
            End If

        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try
        Return functionReturnValue
    End Function

    Public Function Open() As Integer Implements IMDIFunctions.Open
        Dim returnOpen As Integer = 0
        Try
            Dim frmChild As New fSearch

            Dim objDTMaterialSubGroupMaster As New DataLayer.DTMaterialSubGroupMaster

            objDTMaterialSubGroupMaster.CompanyNo = gCompanyNo

            Dim ds As DataSet = objDTMaterialSubGroupMaster.SearchData()

            frmChild.dsSearchDataset = ds
            frmChild.ShowDialog()

            If frmChild.rowId IsNot Nothing Then
                LoadData(Nothing)
                returnOpen = Convert.ToInt16(frmChild.rowId)
            End If
            frmChild.Close()
            frmChild = Nothing

        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try
        Return returnOpen
    End Function

    Public Sub Reset() Implements IMDIFunctions.Reset
        Try
            If gHeadOfficeNo <> gCompanyNo Then
                objBase.UnLockEachControl(Me)

                utxtGroupCode.ReadOnly = True
                utxtCategoryCode.ReadOnly = True
                utxtSubgroupCode.ReadOnly = True
            End If

            bIsReset = True

            objBase.RefreshForm(Me)
            uchkInActive.Enabled = False
            ucmbCategoryName.Focus()
        Catch ex As Exception
            Throw ex
        End Try
    End Sub

    Public Function Save() As IMDIFunctions.SaveReturn Implements IMDIFunctions.Save
        Dim functionReturnValue As IMDIFunctions.SaveReturn = Nothing

        Try
            If ugbFastEntry.Visible Then

                ugdFastEntry.UpdateData()
                Dim band As UltraGridBand = ugdFastEntry.DisplayLayout.Bands(0)

                If objBase.SaveMessage() = False Then
                    For Each ugRow As UltraGridRow In ugdFastEntry.Rows

                        If Convert.ToString(ugRow.GetCellValue(band.Columns("Category Name"))) <> "" Then

                            utxtSubgroupCode.Clear()
                            utxtCode.Clear()

                            ucmbGroupName.Value = Nothing
                            ucmbCategoryName.Value = Nothing

                            Dim mess As String = ""
                            Dim ugCategoryRow As UltraGridRow = objBase.Cell_ValueListResolved(ugRow.Cells("Category Name"))
                            Dim ugGroupRows As DataRow() = objBase.Cell_ValueListResolved(ugRow.Cells("Group Name"), True)


                            If ugCategoryRow IsNot Nothing Then
                                objBase.ControlValueFromProcedure(ucmbCategoryName, ugCategoryRow.Cells("CategoryNo").Value)
                            Else
                                objBase.RefreshForm(ucmbCategoryName)
                            End If
                            If ugGroupRows IsNot Nothing Then
                                For Each row As DataRow In ugGroupRows
                                    If Convert.ToInt32(row("CategoryNo")) = Convert.ToInt32(ugCategoryRow.Cells("CategoryNo").Value) Then
                                        objBase.ControlValueFromProcedure(ucmbGroupName, row("GroupNo"))
                                        Exit For
                                    Else
                                        objBase.RefreshForm(ucmbGroupName)
                                    End If
                                Next
                            Else
                                objBase.RefreshForm(ucmbGroupName)
                            End If


                            If Convert.ToString(ugRow.GetCellValue(band.Columns("Code"))) <> "" Then
                                objBase.ControlValueFromProcedure(utxtCode, ugRow.GetCellValue(band.Columns("Code")))
                            End If

                            objBase.ControlValueFromProcedure(utxtSubGroupName, ugRow.GetCellValue(band.Columns("Sub Group Name")))

                            If ValidateForm() Then
                                Try
                                    functionReturnValue.DocumentNo = SaveMain()
                                    mess = "Successfully Created."
                                Catch ex As Exception
                                    mess = ex.ToString()
                                End Try

                                ugRow.Cells("Remarks").Value = mess
                            Else
                                ugRow.Cells("Remarks").Value = strError
                            End If

                        End If

                    Next

                    objBase.SuccessMessage("Refer remarks for saved status.")
                    objBase.RefreshForm(ugbSubgroupMain)

                End If
            Else

                If ValidateForm() = False Then
                    Return functionReturnValue
                End If

                If objBase.SaveMessage() = False Then
                    functionReturnValue.DocumentNo = SaveMain()
                End If

            End If

        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try
        Return functionReturnValue
    End Function

    Private Function SaveMain() As Object

        Dim SubgroupNo As Int16
        objBase.BeginTransaction()
        Try

            Dim objDTMaterialSubGroupMaster As New DataLayer.DTMaterialSubGroupMaster()

            If objLocalBase.getId() Is Nothing Then
                objDTMaterialSubGroupMaster.SubGroupNo = Nothing
            Else
                objDTMaterialSubGroupMaster.SubGroupNo = Convert.ToInt16(objLocalBase.getId())
            End If

            objDTMaterialSubGroupMaster.CompanyNo = gCompanyNo

            objDTMaterialSubGroupMaster.GroupNo = Convert.ToInt16(ucmbGroupName.Value)
            objDTMaterialSubGroupMaster.Code = utxtCode.Text.Trim

            objDTMaterialSubGroupMaster.SubGroupName = utxtSubGroupName.Text.Trim
            objDTMaterialSubGroupMaster.ReceiptTolerance = Val(utxtReceiptTolerance.Text)

            objDTMaterialSubGroupMaster.ShipmentTolerance = Val(utxtShipmentTolerance.Text)
            objDTMaterialSubGroupMaster.LoginNo = giLoginNo

            objDTMaterialSubGroupMaster.GSTCategoryNo = CType(ucmbGSTCategory.Value, Nullable(Of Byte))
            objDTMaterialSubGroupMaster.HSNSACCodeNo = CType(ucmbHSNSACCode.Value, Nullable(Of Short))

            objDTMaterialSubGroupMaster.IsBINApplicable = uchkBINApplicable.Checked

            If Val(Convert.ToString(utxtDispatchNegTolerance.Value)) <> 0 Then
                objDTMaterialSubGroupMaster.DispatchNegTolerance = Convert.ToDouble(utxtDispatchNegTolerance.Value)
            Else
                objDTMaterialSubGroupMaster.DispatchNegTolerance = Nothing
            End If

            Dim ds As DataSet = objDTMaterialSubGroupMaster.SaveMain()

            Dim dr As DataTableReader = ds.Tables(0).CreateDataReader()

            If dr.Read() Then

                If Convert.ToString(dr(0)) = "0" Then
                    Throw New Exception(Convert.ToString(dr(1)))
                ElseIf Convert.ToString(dr(0)) = "1" Then
                    SubgroupNo = Convert.ToInt16(dr(1))
                End If

                objDTMaterialSubGroupMaster.SubGroupNo = SubgroupNo
            End If
            dr.Close()

            SaveDivision(objDTMaterialSubGroupMaster)
            SaveMake(objDTMaterialSubGroupMaster)

            SaveQC(objDTMaterialSubGroupMaster)
            SaveUnit(objDTMaterialSubGroupMaster)

            SaveVendor(objDTMaterialSubGroupMaster)

            If uchkBINApplicable.Checked = True Then
                SaveBinDetail(objDTMaterialSubGroupMaster)
            End If
            objBase.CommitTransaction()

            If ugbFastEntry.Visible = False Then
                objBase.SavedSuccessMessage()
                NewRecord()
            End If

            SubgroupNo = Convert.ToInt16(objDTMaterialSubGroupMaster.SubGroupNo)

            objDTMaterialSubGroupMaster = Nothing

        Catch ex As Exception

            objBase.RollbackTransaction()
            objBase.ErrorMessage(ex)

        Finally
            objBase.CloseTransaction()
        End Try
        Return SubgroupNo
    End Function

    Public Sub Preview() Implements IMDIFunctions.Preview

    End Sub

    Public Sub Print() Implements IMDIFunctions.Print

    End Sub

    Public Sub FillValues() Implements IMDIFunctions.FillValues
        Try
            SyncLock (objLock)


                Dim objDTMaterialSubGroupMaster As New DataLayer.DTMaterialSubGroupMaster()

                objDTMaterialSubGroupMaster.CompanyNo = gCompanyNo

                If objLocalBase.getId Is Nothing Then
                    objDTMaterialSubGroupMaster.SubGroupNo = Nothing
                Else
                    objDTMaterialSubGroupMaster.SubGroupNo = Convert.ToInt16(objLocalBase.getId())
                End If

                Dim ds As DataSet = objDTMaterialSubGroupMaster.FillValues()

                If bIsReset Then
                    objBase.GrdSetDataSource(ugdDivisionDetail, ds.Tables(0))
                    objBase.GrdSetDataSource(ugdUOM, ds.Tables(3))

                    objBase.GrdSetDataSource(ugdBinDetail, ds.Tables(14))
                    ugdBinDetail.CreationFilter = aCheckBoxOnBinHeader_CreationFilter

                    ulblDispatchNegTolerance.Visible = False
                    utxtDispatchNegTolerance.Visible = False
                    ulblDispatchNegTolerancePer.Visible = False

                    Dim dr As DataTableReader = ds.Tables(15).CreateDataReader
                    If dr.Read AndAlso String.IsNullOrEmpty(Convert.ToString((dr("DisplayDisLotTole")))) = False Then
                        If Convert.ToBoolean(dr("DisplayDisLotTole")) Then
                            ulblDispatchNegTolerance.Visible = True
                            utxtDispatchNegTolerance.Visible = True
                            ulblDispatchNegTolerancePer.Visible = True
                        End If
                    End If

                    bIsReset = False
                End If

                If bIsLoading Then
                    objBase.GrdSetDataSource(ugdMakeDetail, ds.Tables(1))
                    objBase.GrdSetDataSource(ugdVendorDetail, ds.Tables(6))

                    objBase.SetTextBox(utxtReceiptTolerance, EnterType.FloatType, 2)
                    objBase.SetTextBox(utxtShipmentTolerance, EnterType.FloatType, 2)
                    objBase.SetTextBox(utxtDispatchNegTolerance, EnterType.FloatType, 2)

                    objBase.UltraGridColumnDuplicate(ugdMakeDetail, New Object() {"Make Name"}, "Duplicate Make Name not allowed.")
                    objBase.UltraGridColumnDuplicate(ugdVendorDetail, New Object() {"Vendor Name", "Location"}, "Duplicate Vendor Name and Location not allowed.")


                    objBase.GrdSetDataSource(ugdFastEntry, ds.Tables(11))
                    objBase.PopulateValueList(ds.Tables(9), ugdFastEntry, "Category Name", New String() {"Id", "Category Name"})

                    objBase.PopulateValueList(ds.Tables(10), ugdFastEntry, "Group Name", New String() {"Id", "Group Name"})
                    bIsLoading = False

                End If

                objBase.FillControls(ds.Tables(9), ucmbCategoryName, New String() {"CategoryNo", "Category Name", "Code"})

                objBase.PopulateValueList(ds.Tables(2), ugdMakeDetail, "Make Name", New String() {"MakeNo", "Make Name", "Code"})
                objBase.PopulateValueList(ds.Tables(4), ugdUOM, "Unit Type", New String() {"UnitTypeNo", "Unit Type Name"})

                objBase.PopulateValueList(ds.Tables(5), ugdUOM, "Unit Name", New String() {"UnitNo", "Unit Name"})
                objBase.PopulateValueList(ds.Tables(7), ugdVendorDetail, "Vendor Name", New String() {"VendorNo", "Vendor Name"})

                objBase.PopulateValueList(ds.Tables(8), ugdVendorDetail, "Location", New String() {"VendorLocationNo", "Location"})

                objBase.FillControls(ds.Tables(12), ucmbGSTCategory, New String() {"GSTCategoryNo", "Category Name"})
                objBase.FillControls(ds.Tables(13), ucmbHSNSACCode, New String() {"HSNSACCodeNo", "Code", "Description"})

                uQcGroup.FillValues()
            End SyncLock
        Catch ex As Exception
            If TypeOf (ex) Is Threading.ThreadAbortException Then
            Else
                Throw ex
            End If
        End Try
    End Sub

    Private Sub SaveDivision(ByRef objDTMaterialSubGroupMaster As DataLayer.DTMaterialSubGroupMaster)

        Try
            For Each row As DataRow In CType(ugdDivisionDetail.DataSource, DataTable).Select("Select=1 and CompanyNo is not null")

                objDTMaterialSubGroupMaster.WHCompanyNo = Convert.ToByte(row("CompanyNo"))
                objDTMaterialSubGroupMaster.WarehouseNo = Convert.ToInt16(row("WarehouseNo"))
                If Convert.ToString(row("DivisionNo")) <> "" Then
                    objDTMaterialSubGroupMaster.DivisionNo = Convert.ToInt32(row("DivisionNo"))
                Else
                    objDTMaterialSubGroupMaster.DivisionNo = Nothing
                End If

                Dim ds As DataSet = objDTMaterialSubGroupMaster.SaveDivision()
                Dim dr As DataTableReader = ds.Tables(0).CreateDataReader

                If dr.Read Then
                    If Convert.ToString(dr(0)) = "0" Then
                        Throw New Exception(Convert.ToString(dr(1)))
                    End If
                End If
                dr.Close()

            Next
        Catch ex As Exception
            Throw ex
        End Try

    End Sub

    Private Sub SaveMake(ByRef objDTMaterialSubGroupMaster As DataLayer.DTMaterialSubGroupMaster)

        For Each row As UltraGridRow In ugdMakeDetail.Rows
            If Convert.ToString(row.Cells("Make Name").Value) <> "" Then
                objDTMaterialSubGroupMaster.MakeNo = Convert.ToInt16(row.Cells("Make Name").Value)

                Dim ds As DataSet = objDTMaterialSubGroupMaster.SaveMake()
                Dim dr As DataTableReader = ds.Tables(0).CreateDataReader

                If dr.Read Then
                    If Convert.ToString(dr(0)) = "0" Then
                        Throw New Exception(Convert.ToString(dr(1)))
                    End If
                End If
                dr.Close()
            End If
        Next
    End Sub

    Private Sub SaveQC(ByRef objDTMaterialSubGroupMaster As DataLayer.DTMaterialSubGroupMaster)
        Try

            For Each dRow As DataRow In uQcGroup.GridDataSource.Rows
                If Val(Convert.ToString(dRow("QC Parameter Name"))) <> 0 Then
                    objDTMaterialSubGroupMaster.QCParameterNo = Convert.ToInt16(dRow("QC Parameter Name"))
                    objDTMaterialSubGroupMaster.StandardValue = Convert.ToDecimal(dRow("Standard Value"))

                    objDTMaterialSubGroupMaster.ToleranceValue = Convert.ToDecimal(dRow("Tolerance Value"))
                    objDTMaterialSubGroupMaster.DeductionRate = Convert.ToByte(dRow("Deduction Rate"))

                    objDTMaterialSubGroupMaster.DeductionType = Convert.ToByte(dRow("Deduction Type"))

                    If String.IsNullOrEmpty(Convert.ToString(dRow("Double Deduction From"))) Then
                        objDTMaterialSubGroupMaster.DoubleDeductionFrom = Nothing
                    Else
                        objDTMaterialSubGroupMaster.DoubleDeductionFrom = CType(dRow("Double Deduction From"), Short)
                    End If


                    Dim ds As DataSet = objDTMaterialSubGroupMaster.SaveQC
                    Dim dr As DataTableReader = ds.Tables(0).CreateDataReader
                    If dr.Read() Then
                        If dr(0).ToString = "0" Then
                            Throw New Exception(Convert.ToString(dr(1)))
                        End If
                    End If
                    dr.Close()
                End If
            Next

        Catch ex As Exception
            Throw ex
        End Try
    End Sub

    Private Sub SaveUnit(ByRef objDTMaterialSubGroupMaster As DataLayer.DTMaterialSubGroupMaster)

        For Each row As UltraGridRow In ugdUOM.Rows
            If Convert.ToString(row.Cells("Unit Type").Value) <> "" And Convert.ToString(row.Cells("Unit Name").Value) <> "" Then
                objDTMaterialSubGroupMaster.UnitTypeNo = Convert.ToByte(row.Cells("Unit Type").Value)
                objDTMaterialSubGroupMaster.UnitNo = Convert.ToInt16(row.Cells("Unit Name").Value)

                Dim ds As DataSet = objDTMaterialSubGroupMaster.SaveUnit()
                Dim dr As DataTableReader = ds.Tables(0).CreateDataReader

                If dr.Read Then
                    If Convert.ToString(dr(0)) = "0" Then
                        Throw New Exception(Convert.ToString(dr(1)))
                    End If
                End If
                dr.Close()
            End If
        Next
    End Sub

    Private Sub SaveVendor(ByRef objDTMaterialSubGroupMaster As DataLayer.DTMaterialSubGroupMaster)
        For Each row As UltraGridRow In ugdVendorDetail.Rows
            If Convert.ToString(row.Cells("Vendor Name").Value) <> "" Then
                objDTMaterialSubGroupMaster.VendorNo = Convert.ToInt32(row.Cells("Vendor Name").Value)
                objDTMaterialSubGroupMaster.VendorLocationNo = Convert.ToInt32(row.Cells("Location").Value)

                Dim ds As DataSet = objDTMaterialSubGroupMaster.SaveVendor()
                Dim dr As DataTableReader = ds.Tables(0).CreateDataReader

                If dr.Read Then
                    If Convert.ToString(dr(0)) = "0" Then
                        Throw New Exception(Convert.ToString(dr(1)))
                    End If
                End If
                dr.Close()
            End If
        Next
    End Sub

    Private Function FillValuesDependent() As DataSet
        Dim objDTMaterialSubGroupMaster As New DataLayer.DTMaterialSubGroupMaster()

        If ucmbCategoryName.SelectedRow Is Nothing Then
            objDTMaterialSubGroupMaster.CategoryNo = Nothing
        Else
            objDTMaterialSubGroupMaster.CategoryNo = Convert.ToInt16(ucmbCategoryName.Value)
        End If
        If ucmbGroupName.SelectedRow Is Nothing Then
            objDTMaterialSubGroupMaster.GroupNo = Nothing
        Else
            objDTMaterialSubGroupMaster.GroupNo = Convert.ToInt16(ucmbGroupName.Value)
        End If

        Return objDTMaterialSubGroupMaster.FillValuesDependent()

    End Function

    Private Sub ucmbCategoryName_ValueChanged(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles ucmbCategoryName.ValueChanged
        Try
            objBase.RefreshForm(utxtCategoryCode)
            objBase.RefreshForm(ucmbGroupName)

            If ucmbCategoryName.SelectedRow IsNot Nothing Then
                Dim ds As DataSet = FillValuesDependent()
                objBase.FillControls(ds.Tables(0), ucmbGroupName, New String() {"GroupNo", "Group Name", "Code"})

                utxtCategoryCode.Text = Convert.ToString(ucmbCategoryName.SelectedRow.Cells("Code").Value)
            End If
        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try

    End Sub

    Private Sub ugdDivisionDetail_InitializeLayout(ByVal sender As System.Object, ByVal e As Infragistics.Win.UltraWinGrid.InitializeLayoutEventArgs) Handles ugdDivisionDetail.InitializeLayout
        e.Layout.Override.AllowDelete = Infragistics.Win.DefaultableBoolean.False

        e.Layout.Bands(0).Columns("Select").Width = 30
        e.Layout.Bands(0).Columns("warehouse").Width = 350
        e.Layout.Bands(0).Columns("Division").Width = 200

        e.Layout.Bands(0).Columns("Division").CellActivation = Activation.NoEdit
        e.Layout.Bands(0).Columns("warehouse").CellActivation = Activation.NoEdit
        e.Layout.Bands(0).Columns("Company").CellActivation = Activation.NoEdit

        e.Layout.Bands(0).Columns("DivisionNo").Hidden = True
        e.Layout.Bands(0).Columns("WarehouseNo").Hidden = True
        e.Layout.Bands(0).Columns("CompanyNo").Hidden = True

        objBase.Grd_Formatting(CType(sender, UltraGrid))

    End Sub

    Private Sub ugdMakeDetail_AfterCellUpdate(ByVal sender As Object, ByVal e As Infragistics.Win.UltraWinGrid.CellEventArgs) Handles ugdMakeDetail.AfterCellUpdate
        If e.Cell Is Nothing Then
            Exit Sub
        End If
        If e.Cell.Row.Index < 0 Then
            Exit Sub
        End If

        If e.Cell.Row.Index = CType(sender, UltraGrid).Rows.Count - 1 And e.Cell.Column.Key = "Make Name" Then
            CType(sender, UltraGrid).Rows.Band.AddNew()
        End If

        If e.Cell.Column.Key = "Make Name" Then
            Dim row As UltraGridRow = objLocalBase.Cell_ValueListResolved(e.Cell)
            If row IsNot Nothing Then
                e.Cell.Row.Cells("Code").Value = row.Cells("Code").Value
            End If
        End If
    End Sub

    Private Sub ugdMakeDetail_InitializeLayout(ByVal sender As System.Object, ByVal e As Infragistics.Win.UltraWinGrid.InitializeLayoutEventArgs) Handles ugdMakeDetail.InitializeLayout
        e.Layout.Bands(0).Columns("Make Name").Width = 150

        e.Layout.Bands(0).Columns("Code").Width = 100
        e.Layout.Bands(0).Columns("Code").CellActivation = Activation.ActivateOnly

        objBase.Grd_Formatting(CType(sender, UltraGrid))
    End Sub

    Private Sub ugdUOM_InitializeLayout(ByVal sender As System.Object, ByVal e As Infragistics.Win.UltraWinGrid.InitializeLayoutEventArgs) Handles ugdUOM.InitializeLayout
        e.Layout.Override.AllowDelete = Infragistics.Win.DefaultableBoolean.False

        e.Layout.Bands(0).Columns("Unit Type").Width = 100
        e.Layout.Bands(0).Columns("Unit Type").CellActivation = Activation.NoEdit

        e.Layout.Bands(0).Columns("Unit Name").Width = 100

        objBase.Grd_Formatting(CType(sender, UltraGrid))
    End Sub

    Private Sub ugdVendorDetail_AfterCellActivate(ByVal sender As Object, ByVal e As System.EventArgs) Handles ugdVendorDetail.AfterCellActivate

    End Sub

    Private Sub ugdVendorDetail_AfterCellUpdate(ByVal sender As Object, ByVal e As Infragistics.Win.UltraWinGrid.CellEventArgs) Handles ugdVendorDetail.AfterCellUpdate
        If e.Cell Is Nothing Then
            Exit Sub
        End If
        If e.Cell.Row.Index < 0 Then
            Exit Sub
        End If

        If e.Cell.Row.Index = CType(sender, UltraGrid).Rows.Count - 1 And e.Cell.Column.Key = "Vendor Name" Then
            CType(sender, UltraGrid).Rows.Band.AddNew()
        End If

        If e.Cell.Column.Key = "Vendor Name" Then

            e.Cell.Row.Cells("Location").Value = DBNull.Value
            Dim dtLoc As DataTable
            dtLoc = CType(CType(ugdVendorDetail.DisplayLayout.Bands(0).Columns("Location").ValueList, UltraDropDown).DataSource, DataTable)

            If dtLoc.Select("VendorNo=" & Convert.ToString(e.Cell.Row.Cells("Vendor Name").Value)).Length = 1 Then
                e.Cell.Row.Cells("Location").Value = dtLoc.Select("VendorNo=" & Convert.ToString(e.Cell.Row.Cells("Vendor Name").Value))(0).Item("VendorLocationNo")
            End If

        End If
    End Sub

    Private Sub ugdVendorDetail_AfterEnterEditMode(ByVal sender As Object, ByVal e As System.EventArgs) Handles ugdVendorDetail.AfterEnterEditMode
        Dim ugd As UltraGrid = CType(sender, UltraGrid)

        If ugd.ActiveRow Is Nothing Then
            Exit Sub
        End If

        Dim dicFilter As New Dictionary(Of String, Object)
        If ugd.ActiveRow.Cells("Location").Activated Then
            dicFilter.Add("VendorNo", ugd.ActiveRow.Cells("Vendor Name").Value)
            objBase.FilterValueList(ugd, dicFilter)
        End If
    End Sub

    Private Sub ugdVendorDetail_InitializeLayout(ByVal sender As System.Object, ByVal e As Infragistics.Win.UltraWinGrid.InitializeLayoutEventArgs) Handles ugdVendorDetail.InitializeLayout
        e.Layout.Bands(0).Columns("Vendor Name").Width = 200

        e.Layout.Bands(0).Columns("Location").Width = 200

        objBase.Grd_Formatting(CType(sender, UltraGrid))
    End Sub

    Private Sub ucmbGroupName_ValueChanged(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles ucmbGroupName.ValueChanged
        Try
            utxtGroupCode.Clear()
            utxtCode.Clear()
            If ucmbGroupName.SelectedRow IsNot Nothing Then
                utxtGroupCode.Text = Convert.ToString(ucmbGroupName.SelectedRow.Cells("Code").Value)
                Dim ds As DataSet = FillValuesDependent()
                Dim dr As DataTableReader = ds.Tables(1).CreateDataReader
                If dr.Read Then
                    utxtCode.Value = Format(dr("SubGroupCode"), "00")
                End If
                uQcGroup.GridDataSource = ds.Tables(2)
            End If
        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try

    End Sub

    Private Sub GenerateSubGroupCode()
        utxtSubgroupCode.Text = utxtCategoryCode.Text & utxtGroupCode.Text & utxtCode.Text
    End Sub

    Private Sub utxtCode_ValueChanged(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles utxtCode.ValueChanged
        GenerateSubGroupCode()
    End Sub

    Private Sub utxtCategoryCode_ValueChanged(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles utxtCategoryCode.ValueChanged
        GenerateSubGroupCode()
    End Sub

    Private Sub utxtGroupCode_ValueChanged(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles utxtGroupCode.ValueChanged
        GenerateSubGroupCode()
    End Sub

    Public Sub Email(ByVal mailTo As String, ByVal subject As String, ByVal body As String) Implements IMDIFunctions.Email

    End Sub

    Public Sub Export() Implements IMDIFunctions.Export

    End Sub

    Private Sub ufllSubGroupCode_LinkClicked(ByVal sender As System.Object, ByVal e As Infragistics.Win.FormattedLinkLabel.LinkClickedEventArgs) Handles ufllSubGroupCode.LinkClicked
        Try

            NewRecord()
            ugbFastEntry.Visible = True

            ugbFastEntry.Width = 975
            ugbFastEntry.Height = 595

            ugbFastEntry.Top = 3
            ugbFastEntry.Left = 3

        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try

    End Sub

    Private Sub ufllBackFastEntry_LinkClicked(ByVal sender As System.Object, ByVal e As Infragistics.Win.FormattedLinkLabel.LinkClickedEventArgs) Handles ufllBackFastEntry.LinkClicked
        ugbFastEntry.Visible = False
    End Sub

    Private Sub ubtnImport_Click(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles ubtnImport.Click
        Try

            If Not objBase.ConfirmationMessage("Your excel should consists of sheet with name " & Convert.ToString(Me.Tag) & ". Do you want to continue?") Then
                ImportSheet()
            End If

        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try

    End Sub

    Private Sub ugdFastEntry_AfterCellUpdate(ByVal sender As Object, ByVal e As Infragistics.Win.UltraWinGrid.CellEventArgs) Handles ugdFastEntry.AfterCellUpdate

        Try
            If e.Cell Is Nothing Then
                Exit Sub
            End If

            If e.Cell.Row.Index < 0 Then
                Exit Sub
            End If

            Dim Bands As UltraGridBand = ugdFastEntry.DisplayLayout.Bands(0)
            If e.Cell.Row.Index = ugdFastEntry.Rows.Count - 1 AndAlso e.Cell.IsInEditMode Then
                ugdFastEntry.Rows.Band.AddNew()
            End If

            If e.Cell.Column.Key = "Category Name" Then
                e.Cell.Row.Cells("Group Name").Value = DBNull.Value
            End If

        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try

    End Sub

    Private Sub ugdFastEntry_AfterEnterEditMode(ByVal sender As Object, ByVal e As System.EventArgs) Handles ugdFastEntry.AfterEnterEditMode
        Try

            Dim ugCell As UltraGridCell = ugdFastEntry.ActiveCell
            If ugCell Is Nothing Then
                Exit Sub
            End If

            If ugCell.Column.Key = "Group Name" Then

                Dim row As UltraGridRow = objBase.Cell_ValueListResolved(ugCell.Row.Cells("Category Name"))

                If row IsNot Nothing Then
                    objBase.FilterValueList(ugdFastEntry, "CategoryNo", row.Cells("CategoryNo").Value)
                End If

            End If

        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try

    End Sub

    Private Sub ugdFastEntry_InitializeLayout(ByVal sender As Object, ByVal e As Infragistics.Win.UltraWinGrid.InitializeLayoutEventArgs) Handles ugdFastEntry.InitializeLayout
        Try

            Dim band As UltraGridBand = e.Layout.Bands(0)
            band.Columns("Remarks").CellActivation = Activation.ActivateOnly
            band.Columns("Remarks").Width = 283

            band.Columns("Category Name").Width = 152
            band.Columns("Group Name").Width = 164

            band.Columns("Code").Width = 86
            band.Columns("Sub Group Name").Width = 236

            band.Columns("Sub Group Name").MaxLength = 100
            band.Columns("Code").MaxLength = 2

            objBase.Grd_Formatting(CType(sender, UltraGrid))

        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try

    End Sub

    Private Sub ucmbHSNSACCode_ValueChanged(sender As System.Object, e As System.EventArgs) Handles ucmbHSNSACCode.ValueChanged
        utxtCGSTRate.Value = ""
        utxtSGSTRate.Value = ""
        utxtIGSTRate.Value = ""
        utxtUTGSTRate.Value = ""
        If ucmbHSNSACCode.SelectedRow IsNot Nothing Then
            utxtCGSTRate.Value = ucmbHSNSACCode.SelectedRow.Cells("CGST").Value
            utxtSGSTRate.Value = ucmbHSNSACCode.SelectedRow.Cells("SGST").Value
            utxtIGSTRate.Value = ucmbHSNSACCode.SelectedRow.Cells("IGST").Value
            utxtUTGSTRate.Value = ucmbHSNSACCode.SelectedRow.Cells("UTGST").Value
        End If
    End Sub

    Private Sub SaveBinDetail(ByRef objDTMaterialSubGroupMaster As DataLayer.DTMaterialSubGroupMaster)
        ugdBinDetail.UpdateData()
        For Each row As UltraGridRow In ugdBinDetail.Rows
            If Convert.ToString(row.Cells("BinNo").Value) <> "" AndAlso Convert.ToBoolean(row.Cells("Select").Value) = True Then
                objDTMaterialSubGroupMaster.BinNo = Convert.ToInt16(row.Cells("BinNo").Value)

                Dim ds As DataSet = objDTMaterialSubGroupMaster.SaveBinDetail()
                Dim dr As DataTableReader = ds.Tables(0).CreateDataReader

                If dr.Read Then
                    If Convert.ToString(dr(0)) = "0" Then
                        Throw New Exception(Convert.ToString(dr(1)))
                    End If
                End If
                dr.Close()
            End If
        Next
    End Sub

    Private Sub ugdBinDetail_InitializeLayout(ByVal sender As Object, ByVal e As Infragistics.Win.UltraWinGrid.InitializeLayoutEventArgs) Handles ugdBinDetail.InitializeLayout
        Try
            e.Layout.Bands(0).Columns("BinNo").Hidden = True
            e.Layout.Bands(0).Columns("Bin Card No.").CellActivation = Activation.NoEdit
            e.Layout.Bands(0).Columns("Location").CellActivation = Activation.NoEdit
            e.Layout.Bands(0).Columns("Warehouse").CellActivation = Activation.NoEdit
            e.Layout.Bands(0).Columns("Select").Header.Caption = ""
            e.Layout.Bands(0).Columns("Select").DefaultCellValue = False
            objBase.Grd_Formatting(CType(sender, UltraGrid))
        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try

    End Sub

    Private Sub uchkBINApplicable_CheckedChanged(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles uchkBINApplicable.CheckedChanged
        If uchkBINApplicable.Checked = True Then
            utabMain.Tabs("BD").Visible = True
        Else
            utabMain.Tabs("BD").Visible = False
        End If
    End Sub
End Class