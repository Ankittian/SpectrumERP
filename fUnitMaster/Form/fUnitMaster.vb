Imports System.Data.SqlClient
Imports BaseArchitecture.BusinessLogicLayer.ClsCommonFunction
Imports System.Threading
Imports Infragistics.Win.UltraWinGrid

Public Class fUnitMaster
    Implements IMDIFunctions

    Dim bIsLoading As Boolean
    Dim strError As String

    Private Sub fUnitMaster_Load(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles MyBase.Load
        Try
            dicOptions.Item(Me) = New Integer(4) {}

            dicOptions.Item(Me)(0) = ToolBarOption.New
            dicOptions.Item(Me)(1) = ToolBarOption.Save
            dicOptions.Item(Me)(2) = ToolBarOption.Open
            dicOptions.Item(Me)(3) = ToolBarOption.Delete
            dicOptions.Item(Me)(4) = ToolBarOption.Navigation
            objBase.CompulsaryField(New Control() {utxtUnitName, ucmbCategory, utxtAlias})

            ufllCode.Value = "<a title=""Switch to fast entry mode."">Code</a>"
            ufllCode.ShowTitleToolTips = True

            ufllCode.Height = 20
            ufllBackFastEntry.Height = 20

            bIsLoading = True
        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try
    End Sub
    Public Function Delete() As Boolean Implements IMDIFunctions.Delete
        Dim functionReturnValue As Boolean = False
        Try

            If objLocalBase.getId() Is Nothing Then
                Return False
            End If

            If objBase.DeleteMessage = False Then
                Dim ObjDTUnitMaster As New SpectrumERP.DataLayer.DTUnitMaster()

                ObjDTUnitMaster.UnitNo = CType(objLocalBase.getId(), Short)
                Dim dr As DataTableReader = ObjDTUnitMaster.Delete().CreateDataReader

                If dr.Read() Then
                    If dr.Item(0).ToString = "1" Then
                        objBase.DeleteSuccessMessage()
                        functionReturnValue = True
                        NewRecord()
                    Else
                        objBase.DeleteValidationMessage(dr(1).ToString)
                    End If
                End If
                dr.Close()
            End If
        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try
    End Function

    Public Sub FillValues() Implements IMDIFunctions.FillValues
        Try
            SyncLock (objLock)

                Dim ObjDTUnitMaster As New SpectrumERP.DataLayer.DTUnitMaster
                ObjDTUnitMaster.CompanyNo = CType(gCompanyNo, Byte)
                ObjDTUnitMaster.UnitNo = CType(objLocalBase.getId, Short)
                Dim ds As DataSet = ObjDTUnitMaster.FillValues

                If bIsLoading Then
                    objBase.GrdSetDataSource(ugdStandardConversionFactor, ds.Tables(1))
                    objBase.GrdSetDataSource(ugdMaterialSubgroup, ds.Tables(4))

                    objBase.PopulateValueList(ds.Tables(2), ugdStandardConversionFactor, "Conversion Type", New String() {"ID", "Conversion Type"})
                    objBase.PopulateValueList(ds.Tables(6), ugdMaterialSubgroup, "Unit Type", New String() {"UnitTypeNo", "Unit Type"})

                    objBase.UltraGridColumnText(ugdStandardConversionFactor, "Unit Value", 11, EnterType.FloatType, 3)
                    objBase.UltraGridColumnText(ugdStandardConversionFactor, "Conversion Value", 11, EnterType.FloatType, 3)

                    objBase.UltraGridColumnDuplicate(ugdStandardConversionFactor, New String() {"Unit"}, "Duplicate Unit is not allowed.")
                    objBase.UltraGridColumnDuplicate(ugdMaterialSubgroup, New String() {"Subgroup Name"}, "Duplicate Subgroup Name is not allowed.")

                    objBase.GrdSetDataSource(ugdFastEntry, ds.Tables(7))
                    objBase.PopulateValueList(ds.Tables(0), ugdFastEntry, "Category", New String() {"Id", "Category Name"})

                    bIsLoading = False
                End If
                objBase.FillControls(ds.Tables(0), ucmbCategory, New String() {"UnitCategoryno", "Category Name"})
                objBase.FillControls(ds.Tables(8), ucmbGSTUQC, New String() {"GSTUnitNo", "Code", "Unit Name"})
                objBase.PopulateValueList(ds.Tables(3), ugdStandardConversionFactor, "Unit", New String() {"UnitNo", "Alias", "Unit Name", "Code"})
                objBase.PopulateValueList(ds.Tables(5), ugdMaterialSubgroup, "Subgroup Name", New String() {"SubGroupNo", "SubGroup Name", "Group Name", "Code"})

            End SyncLock
        Catch ex As Exception
            If TypeOf (ex) Is ThreadAbortException Then
            Else
                Throw ex
            End If
        End Try


    End Sub

    Public Sub LoadData(ByVal optionalValue As Object) Implements IMDIFunctions.LoadData
        Try
            Reset()
            FillValues()

            Dim ObjDTUnitMaster As New SpectrumERP.DataLayer.DTUnitMaster()

            ObjDTUnitMaster.UnitNo = CType(objLocalBase.getId, Short)
            ObjDTUnitMaster.CompanyNo = gCompanyNo
            Dim ds As DataSet = ObjDTUnitMaster.LoadData()

            Dim dr As DataTableReader = ds.Tables(0).CreateDataReader()
            If dr.Read() Then
                objBase.ControlValueFromProcedure(utxtUnitName, dr("UnitName"))
                objBase.ControlValueFromProcedure(utxtUnitCode, dr("Code"))

                objBase.ControlValueFromProcedure(utxtAlias, dr("Alias"))
                objBase.ControlValueFromProcedure(uchkInactive, dr("InActive"))
                objBase.ControlValueFromProcedure(ucmbCategory, dr("UnitCategoryNo"))
                objBase.ControlValueFromProcedure(ucmbGSTUQC, dr("GSTUnitNo"))
            End If
            dr.Close()

            objBase.GrdSetDataSource(ugdStandardConversionFactor, ds.Tables(1))
            objBase.GrdSetDataSource(ugdMaterialSubgroup, ds.Tables(2))
        Catch ex As Exception
            Throw ex
        End Try
    End Sub

    Public Sub NewRecord() Implements IMDIFunctions.NewRecord
        Try
            Dim frm As mdiProject = CType(Me.MdiParent, mdiProject)
            frm.NewRecord()
            utxtUnitName.Focus()
        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try
    End Sub

    Public Function Open() As Integer Implements IMDIFunctions.Open
        Dim returnOpen As Integer = 0
        Try
            Dim frmChild As New fSearch
            Dim ObjDTUnitMaster As New SpectrumERP.DataLayer.DTUnitMaster()

            ObjDTUnitMaster.CompanyNo = CType(gCompanyNo, Byte)
            Dim ds As DataSet = ObjDTUnitMaster.SearchData()

            frmChild.dsSearchDataset = ds
            frmChild.ShowDialog()

            If frmChild.rowId IsNot Nothing Then
                LoadData(Nothing)
                returnOpen = Convert.ToInt32(frmChild.rowId)
            End If
            frmChild = Nothing

        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try
    End Function

    Public Sub Preview() Implements IMDIFunctions.Preview

    End Sub

    Public Sub Print() Implements IMDIFunctions.Print

    End Sub

    Public Sub Reset() Implements IMDIFunctions.Reset

        Try
            objBase.RefreshForm(Me)
            utxtUnitName.Focus()
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
                        If Convert.ToString(ugRow.GetCellValue(band.Columns("Unit Name"))) <> "" Then

                            objBase.RefreshForm(ugbMain)

                            Dim mess As String = ""
                            Dim ugdUnitRow As UltraGridRow = objBase.Cell_ValueListResolved(ugRow.Cells("Category"))

                            If ugdUnitRow IsNot Nothing Then
                                objBase.ControlValueFromProcedure(ucmbCategory, ugdUnitRow.Cells("UnitCategoryno").Value)
                            Else
                                objBase.RefreshForm(ucmbCategory)
                            End If

                            objBase.ControlValueFromProcedure(utxtUnitName, ugRow.Cells("Unit Name").Value)
                            objBase.ControlValueFromProcedure(utxtAlias, ugRow.Cells("Alias").Value)

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
                    objBase.RefreshForm(ugbMain)
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

    Private Sub SaveConversionFactor(ByVal ObjDTUnitMaster As SpectrumERP.DataLayer.DTUnitMaster)
        Try
            Dim dr As DataTableReader
            Dim Bands As UltraGridBand

            Bands = ugdStandardConversionFactor.DisplayLayout.Bands(0)
            For Each ugdRow As UltraGridRow In ugdStandardConversionFactor.Rows
                If Val(Convert.ToString(ugdRow.GetCellValue(Bands.Columns("Conversion Type")))) <> 0 Then
                    ObjDTUnitMaster.ConversionType = ugdRow.GetCellValue(Bands.Columns("Conversion Type"))
                    ObjDTUnitMaster.FirstCF = ugdRow.GetCellValue(Bands.Columns("Unit Value"))

                    ObjDTUnitMaster.SecondCF = ugdRow.GetCellValue(Bands.Columns("Conversion Value"))
                    ObjDTUnitMaster.ConversionUnitNo = ugdRow.GetCellValue(Bands.Columns("Unit"))

                    dr = ObjDTUnitMaster.SaveUnitConversionDetail.CreateDataReader
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

    Private Sub SaveSubGroupUnitDetail(ByVal ObjDTUnitMaster As SpectrumERP.DataLayer.DTUnitMaster)
        Try
            Dim dr As DataTableReader
            Dim Bands As UltraGridBand

            Bands = ugdMaterialSubgroup.DisplayLayout.Bands(0)
            For Each ugdRow As UltraGridRow In ugdMaterialSubgroup.Rows
                If Val(Convert.ToString(ugdRow.GetCellValue(Bands.Columns("Subgroup Name")))) <> 0 Then
                    ObjDTUnitMaster.SubGroupNo = ugdRow.GetCellValue(Bands.Columns("Subgroup Name"))
                    ObjDTUnitMaster.UnitTypeNo = ugdRow.GetCellValue(Bands.Columns("Unit Type"))

                    dr = ObjDTUnitMaster.SaveSubGroupUnitDetail.CreateDataReader
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

    Private Function ValidateForm() As Boolean

        ValidateForm = False
        strError = Nothing
        ugdFastEntry.UpdateData()

        ugdStandardConversionFactor.UpdateData()
        ugdMaterialSubgroup.UpdateData()

        If utxtUnitName.Text.Trim = "" Then

            If ugbFastEntry.Visible = False Then

                objBase.ValidationMessage("Enter Unit Name.")
                utxtUnitName.Focus()
            Else
                strError = "Enter Unit Name."
            End If

            Exit Function

        Else
            Dim ObjDTUnitMaster As New SpectrumERP.DataLayer.DTUnitMaster()
            ObjDTUnitMaster.UnitNo = CType(objLocalBase.getId, Short)

            ObjDTUnitMaster.UnitName = utxtUnitName.Text.Trim
            ObjDTUnitMaster.CompanyNo = gCompanyNo

            ObjDTUnitMaster.UnitName = utxtUnitName.Text.Trim
            ObjDTUnitMaster.Alias = utxtAlias.Text.Trim

            Dim dr As DataTableReader = ObjDTUnitMaster.Validate().CreateDataReader
            If dr.Read() Then
                If dr(0).ToString = "0" Then
                    If dr(2).ToString = "1" Then

                        If ugbFastEntry.Visible = False Then
                            objBase.FormValidation(dr(1).ToString) 'Duplicate Unit
                            utxtUnitName.Focus()
                        Else
                            strError = Convert.ToString(dr(1))
                        End If
                        ValidateForm = False
                        Exit Function
                    Else

                        If ugbFastEntry.Visible = False Then
                            objBase.FormValidation(dr(1).ToString) 'Duplicate Alias
                            utxtAlias.Focus()
                        Else
                            strError = Convert.ToString(dr(1))
                        End If
                        ValidateForm = False
                        Exit Function
                    End If

                End If
            End If
            dr.Close()
        End If


        If utxtAlias.Text.Trim = "" Then

            If ugbFastEntry.Visible = False Then
                objBase.ValidationMessage("Enter Alias.")
                utxtAlias.Focus()
            Else
                strError = "Enter Alias."
            End If

            Return False
        End If

        If ucmbCategory.SelectedRow Is Nothing Then

            If ugbFastEntry.Visible = False Then
                objBase.ValidationMessage("Select valid Category Name.")
                ucmbCategory.Focus()
            Else
                strError = "Select valid Category Name."
            End If
            Exit Function

        End If

            Dim Bands As UltraGridBand
            Bands = ugdStandardConversionFactor.DisplayLayout.Bands(0)

            ' Validation Of Conversion Factor
            For Each ugdRow As UltraGridRow In ugdStandardConversionFactor.Rows

                If Val(Convert.ToString(ugdRow.GetCellValue(Bands.Columns("Conversion Type")))) <> 0 Then

                    If Val(Convert.ToString(ugdRow.GetCellValue(Bands.Columns("Unit Value")))) = 0.0 Then
                        objBase.ValidationMessage("Enter Unit Value in row " & ugdRow.VisibleIndex + 1 & ".")
                        ugdStandardConversionFactor.Focus()
                        ugdStandardConversionFactor.ActiveCell = ugdRow.Cells("Unit Value")
                        ugdStandardConversionFactor.PerformAction(UltraGridAction.EnterEditMode)
                        Exit Function
                    End If

                    If Val(Convert.ToString(ugdRow.GetCellValue(Bands.Columns("Conversion Value")))) = 0.0 Then
                        objBase.ValidationMessage("Enter Conversion Value in row " & ugdRow.VisibleIndex + 1 & ".")
                        ugdStandardConversionFactor.Focus()
                        ugdStandardConversionFactor.ActiveCell = ugdRow.Cells("Conversion Value")
                        ugdStandardConversionFactor.PerformAction(UltraGridAction.EnterEditMode)
                        Exit Function
                    End If

                    If Val(Convert.ToString(ugdRow.GetCellValue(Bands.Columns("Unit")))) = 0 Then
                        objBase.ValidationMessage("Enter Unit in row " & ugdRow.VisibleIndex + 1 & ".")
                        ugdStandardConversionFactor.Focus()
                        ugdStandardConversionFactor.ActiveCell = ugdRow.Cells("Unit")
                        ugdStandardConversionFactor.PerformAction(UltraGridAction.EnterEditMode)
                        Exit Function
                    End If
                End If
            Next

            Bands = ugdMaterialSubgroup.DisplayLayout.Bands(0)
            ' Validation Of Material SubGroup
            For Each ugdRow As UltraGridRow In ugdMaterialSubgroup.Rows
                If Val(Convert.ToString(ugdRow.GetCellValue(Bands.Columns("Subgroup Name")))) <> 0 Then
                    If Val(Convert.ToString(ugdRow.GetCellValue(Bands.Columns("Unit Type")))) = 0 Then
                        objBase.ValidationMessage("Select valid Unit Type in row " & ugdRow.VisibleIndex + 1 & ".")
                        ugdMaterialSubgroup.Focus()
                        ugdMaterialSubgroup.ActiveCell = ugdRow.Cells("Unit Type")
                        ugdMaterialSubgroup.PerformAction(UltraGridAction.EnterEditMode)
                        Exit Function
                    End If
                End If
            Next

            ValidateForm = True
    End Function

    Private Sub ugdStandardConversionFactor_InitializeLayout(ByVal sender As System.Object, ByVal e As Infragistics.Win.UltraWinGrid.InitializeLayoutEventArgs) Handles ugdStandardConversionFactor.InitializeLayout
        Try
            Dim Bands As UltraGridBand = e.Layout.Bands(0)
            Bands.Columns("Base Unit").CellActivation = Activation.NoEdit
            Bands.Columns("Base Unit").Width = 50

            Bands.Columns("Base Unit").TabStop = False
            Bands.Columns("Conversion Value").Width = 100

            Bands.Columns("Conversion Type").Width = 80
            Bands.Columns("Unit").Width = 110
        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try
    End Sub

    Private Sub ugdMaterialSubgroup_InitializeLayout(ByVal sender As System.Object, ByVal e As Infragistics.Win.UltraWinGrid.InitializeLayoutEventArgs) Handles ugdMaterialSubgroup.InitializeLayout
        Try
            Dim Bands As UltraGridBand = e.Layout.Bands(0)
            Bands.Columns("Subgroup Code").CellActivation = Activation.NoEdit
            Bands.Columns("Subgroup Code").Width = 70

            Bands.Columns("Subgroup Code").TabStop = False
            Bands.Columns("Unit Type").Width = 120
            Bands.Columns("Subgroup Name").Width = 100
        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try
    End Sub

    Private Sub ugdMaterialSubgroup_AfterCellUpdate(ByVal sender As System.Object, ByVal e As Infragistics.Win.UltraWinGrid.CellEventArgs) Handles ugdMaterialSubgroup.AfterCellUpdate
        Try
            Dim Bands As UltraGridBand = ugdMaterialSubgroup.DisplayLayout.Bands(0)
            If e.Cell.Row.Index = ugdMaterialSubgroup.Rows.Count - 1 Then
                ugdMaterialSubgroup.Rows.Band.AddNew()
            End If

            If e.Cell.Column.Key = "Subgroup Name" Then
                e.Cell.Row.Cells("Subgroup Code").Value = ""
                If Val(Convert.ToString(e.Cell.Row.GetCellValue(Bands.Columns("Subgroup Name")))) <> 0 Then
                    Dim ugdRow As UltraGridRow = objBase.Cell_ValueListResolved(e.Cell.Row.Cells("Subgroup Name"))
                    e.Cell.Row.Cells("Subgroup Code").Value = ugdRow.Cells("Code").Value
                End If
            End If
        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try
    End Sub

    Private Sub ugdStandardConversionFactor_AfterCellUpdate(ByVal sender As System.Object, ByVal e As Infragistics.Win.UltraWinGrid.CellEventArgs) Handles ugdStandardConversionFactor.AfterCellUpdate
        Try
            If e.Cell Is Nothing Then
                Return
            End If

            If e.Cell.Column.Key <> "Base Unit" Then
                If e.Cell.Row.Index = ugdStandardConversionFactor.Rows.Count - 1 Then
                    ugdStandardConversionFactor.Rows.Band.AddNew()
                End If
            End If
        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try
    End Sub

    Private Sub ugdStandardConversionFactor_InitializeRow(ByVal sender As System.Object, ByVal e As Infragistics.Win.UltraWinGrid.InitializeRowEventArgs) Handles ugdStandardConversionFactor.InitializeRow
        Try
            If utxtAlias.Text.Trim <> "" Then
                e.Row.Cells("Base Unit").Value = utxtAlias.Text.Trim
            End If
        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try
    End Sub

    Private Sub utxtAlias_ValueChanged(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles utxtAlias.ValueChanged
        Try
            For Each ugdRow As UltraGridRow In ugdStandardConversionFactor.Rows
                ugdRow.Cells("Base Unit").Value = utxtAlias.Text.Trim
            Next
        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try
    End Sub

    Public Sub Email(ByVal mailTo As String, ByVal subject As String, ByVal body As String) Implements IMDIFunctions.Email

    End Sub

    Public Sub Export() Implements IMDIFunctions.Export

    End Sub

    Private Sub ufllCode_LinkClicked(ByVal sender As Object, ByVal e As Infragistics.Win.FormattedLinkLabel.LinkClickedEventArgs) Handles ufllCode.LinkClicked

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

    Private Sub ubtnImport_Click(ByVal sender As Object, ByVal e As System.EventArgs) Handles ubtnImport.Click
        Try

            If Not objBase.ConfirmationMessage("Your excel should consists of sheet with name " & Convert.ToString(Me.Tag) & ". Do you want to continue?") Then
                ImportSheet()
            End If

        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try
    End Sub

    Private Sub ImportSheet()
        Try

            Dim objclsReadExcelFile As New clsReadExcelFile
            Dim dt As DataTable = objclsReadExcelFile.GetExcelSheetDetail

            If clsReadExcelFile.strFilePath <> "" Then

                objBase.RefreshForm(ugdFastEntry)

                objclsReadExcelFile.strColumnNames = New String() {"Unit Name", "Alias", "Category"}

                Dim dtImported As DataTable = objclsReadExcelFile.GetSheetTable(Convert.ToString(Me.Tag) & "$")

                dtImported.Columns.Add("Remarks")
                dtImported.AcceptChanges()

                objBase.GrdSetDataSource(ugdFastEntry, dtImported)

            End If

        Catch ex As Exception
            Throw ex
        End Try
    End Sub

    Private Function SaveMain() As Object

        Dim iUnitNo As Int32
        objBase.BeginTransaction()

        Try
            Dim ObjDTUnitMaster As New SpectrumERP.DataLayer.DTUnitMaster()

            ObjDTUnitMaster.UnitNo = CType(objLocalBase.getId(), Short)
            ObjDTUnitMaster.CompanyNo = CType(gCompanyNo, Byte)

            ObjDTUnitMaster.LoginNo = giLoginNo
            ObjDTUnitMaster.UnitName = utxtUnitName.Text.Trim

            ObjDTUnitMaster.Alias = utxtAlias.Text.Trim
            ObjDTUnitMaster.UnitCategoryNo = CType(ucmbCategory.Value, Short)

            ObjDTUnitMaster.Inactive = CType(uchkInactive.CheckedValue, Boolean)

            If ucmbGSTUQC.SelectedRow Is Nothing Then
                ObjDTUnitMaster.GSTUQC = Nothing
            Else
                ObjDTUnitMaster.GSTUQC = Convert.ToInt16(ucmbGSTUQC.Value)
            End If
            Dim dr As DataTableReader = ObjDTUnitMaster.Save().CreateDataReader

            If dr.Read() Then
                If dr(0).ToString = "0" Then

                    Throw New Exception(dr(1).ToString)
                Else

                    ObjDTUnitMaster.UnitNo = dr(1)
                    iUnitNo = CType(dr(1), Int32)

                End If
            End If
            dr.Close()

            SaveConversionFactor(ObjDTUnitMaster)
            SaveSubGroupUnitDetail(ObjDTUnitMaster)

            objBase.CommitTransaction()

            If ugbFastEntry.Visible = False Then
                objBase.SavedSuccessMessage()
                NewRecord()
            End If

            ObjDTUnitMaster = Nothing

            Return iUnitNo

        Catch ex As Exception

            objBase.RollbackTransaction()
            objBase.ErrorMessage(ex)

        Finally
            objBase.CloseTransaction()
        End Try

    End Function

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

        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try

    End Sub

    Private Sub ugdFastEntry_InitializeLayout(ByVal sender As Object, ByVal e As Infragistics.Win.UltraWinGrid.InitializeLayoutEventArgs) Handles ugdFastEntry.InitializeLayout

        Try

            Dim band As UltraGridBand = e.Layout.Bands(0)
            band.Columns("Remarks").CellActivation = Activation.ActivateOnly

            band.Columns("Unit Name").Width = 100
            band.Columns("Category").Width = 150

            band.Columns("Remarks").Width = 372
            band.Columns("Alias").Width = 40

            band.Columns("Unit Name").MaxLength = 25
            band.Columns("Alias").MaxLength = 6

            objBase.Grd_Formatting(CType(sender, UltraGrid))

        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try

    End Sub

    Private Sub ufllBackFastEntry_LinkClicked(ByVal sender As Object, ByVal e As Infragistics.Win.FormattedLinkLabel.LinkClickedEventArgs) Handles ufllBackFastEntry.LinkClicked
        ugbFastEntry.Visible = False
    End Sub
End Class