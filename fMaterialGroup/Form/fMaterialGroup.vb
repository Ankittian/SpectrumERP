Imports BaseArchitecture.BusinessLogicLayer.ClsCommonFunction
Imports System.Threading
Imports Infragistics.Win.UltraWinGrid

Public Class fMaterialGroup
    Implements IMDIFunctions

    Dim bIsLoading As Boolean = True
    Dim strError As String

    Private Sub ImportSheet()
        Try
            Dim objclsReadExcelFile As New clsReadExcelFile
            Dim dt As DataTable = objclsReadExcelFile.GetExcelSheetDetail

            If clsReadExcelFile.strFilePath <> "" Then

                objBase.RefreshForm(ugdFastEntry)
                objclsReadExcelFile.strColumnNames = New String() {"Category Name", "Code", "Group Name"}

                Dim dtImported As DataTable = objclsReadExcelFile.GetSheetTable(Convert.ToString(Me.Tag) & "$")

                dtImported.Columns.Add("Remarks")
                dtImported.AcceptChanges()

                objBase.GrdSetDataSource(ugdFastEntry, dtImported)

            End If

        Catch ex As Exception
            Throw ex
        End Try

    End Sub

    Private Sub fMaterialGroup_Load(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles MyBase.Load
        Try
            dicOptions.Item(Me) = New Integer(4) {}
            dicOptions.Item(Me)(0) = ToolBarOption.New

            dicOptions.Item(Me)(1) = ToolBarOption.Save
            dicOptions.Item(Me)(2) = ToolBarOption.Open

            dicOptions.Item(Me)(3) = ToolBarOption.Delete
            dicOptions.Item(Me)(4) = ToolBarOption.Navigation

            objBase.CompulsaryField(New Control() {ucmbCategoryName, utxtCode, utxtGroupName})

            ufllCode.Value = "<a title=""Switch to fast entry mode."">Group Code</a>"
            ufllCode.ShowTitleToolTips = True

            ufllCode.Height = 20
            ufllBackFastEntry.Height = 20

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
                Dim ObjDTMaterialGroup As New SpectrumERP.DataLayer.DTMaterialGroup()
                ObjDTMaterialGroup.GroupNo = CType(objLocalBase.getId(), Short)

                Dim dr As DataTableReader = ObjDTMaterialGroup.Delete().CreateDataReader
                If dr.Read() Then
                    If dr(0).ToString = "0" Then
                        objBase.DeleteValidationMessage(dr(1).ToString)
                    Else
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

    Public Sub FillValues() Implements IMDIFunctions.FillValues
        Try
            SyncLock (objLock)
                Dim ObjDTMaterialGroup As New SpectrumERP.DataLayer.DTMaterialGroup
                ObjDTMaterialGroup.CompanyNo = gCompanyNo

                ObjDTMaterialGroup.GroupNo = CType(objLocalBase.getId, Short)
                Dim ds As DataSet = ObjDTMaterialGroup.FillValues

                If bIsLoading Then

                    objBase.GrdSetDataSource(ugdFastEntry, ds.Tables(1))
                    objBase.PopulateValueList(ds.Tables(0), ugdFastEntry, "Category Name", New String() {"Id", "Category Name"})
                    bIsLoading = False

                End If

                objBase.FillControls(ds.Tables(0), ucmbCategoryName, New String() {"CategoryNo", "Category Name", "Code"})
                QcGroup.FillValues()

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

            Dim ObjDTMaterialGroup As New SpectrumERP.DataLayer.DTMaterialGroup()
            ObjDTMaterialGroup.GroupNo = CType(objLocalBase.getId, Short)
            ObjDTMaterialGroup.CompanyNo = gCompanyNo

            Dim ds As DataSet = ObjDTMaterialGroup.LoadData()
            Dim dr As DataTableReader = ds.Tables(0).CreateDataReader()

            If dr.Read() Then
                objBase.ControlValueFromProcedure(ucmbCategoryName, dr("CategoryNo"))
                objBase.ControlValueFromProcedure(utxtCode, dr("GroupCode"))

                objBase.ControlValueFromProcedure(utxtGroupName, dr("GroupName"))
                objBase.ControlValueFromProcedure(uchkInactive, dr("InActive"))
            End If
            If gCompanyNo <> gHeadOfficeNo Then
                objBase.LockEachControl(Me)
            End If

            dr.Close()
            QcGroup.GridDataSource = ds.Tables(1)
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

    Public Function Open() As Integer Implements IMDIFunctions.Open
        Dim returnOpen As Integer = 0
        Try
            Dim frmChild As New fSearch
            Dim ObjDTMaterialGroup As New SpectrumERP.DataLayer.DTMaterialGroup()

            ObjDTMaterialGroup.CompanyNo = CType(gCompanyNo, Byte)
            Dim ds As DataSet = ObjDTMaterialGroup.SearchData()

            frmChild.dsSearchDataset = ds
            frmChild.ShowDialog()

            If frmChild.rowId IsNot Nothing Then
                LoadData(Nothing)
                returnOpen = Convert.ToInt32(frmChild.rowId)
            End If
            frmChild.Close()
            frmChild = Nothing

        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try
        Return returnOpen
    End Function

    Public Sub Preview() Implements IMDIFunctions.Preview

    End Sub

    Public Sub Print() Implements IMDIFunctions.Print

    End Sub

    Public Sub Reset() Implements IMDIFunctions.Reset

        Try
            objBase.RefreshForm(Me)
            If gCompanyNo <> gHeadOfficeNo Then
                objBase.LockEachControl(Me)
            End If
            uchkInactive.Enabled = False
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

                            utxtGroupCode.Clear()
                            utxtCode.Clear()

                            ucmbCategoryName.Value = Nothing
                            Dim mess As String = ""

                            Dim ugCategoryRow As UltraGridRow = objBase.Cell_ValueListResolved(ugRow.Cells("Category Name"))

                            If ugCategoryRow IsNot Nothing Then
                                objBase.ControlValueFromProcedure(ucmbCategoryName, ugCategoryRow.Cells("CategoryNo").Value)
                            Else
                                objBase.RefreshForm(ucmbCategoryName)
                            End If

                            If Convert.ToString(ugRow.GetCellValue(band.Columns("Code"))) <> "" Then
                                objBase.ControlValueFromProcedure(utxtCode, ugRow.GetCellValue(band.Columns("Code")))
                            End If

                            objBase.ControlValueFromProcedure(utxtGroupName, ugRow.GetCellValue(band.Columns("Group Name")))

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

                    objBase.SuccessMessage("Refer Remarks for data saved status.")
                    objBase.RefreshForm(ugbMaterialGroup)

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

        Dim GroupNo As Int16
        objBase.BeginTransaction()

        Try
            Dim ObjDTMaterialGroup As New SpectrumERP.DataLayer.DTMaterialGroup()

            ObjDTMaterialGroup.GroupNo = CType(objLocalBase.getId(), Short)
            ObjDTMaterialGroup.LoginNo = giLoginNo

            ObjDTMaterialGroup.CategoryNo = CType(ucmbCategoryName.Value, Short)
            ObjDTMaterialGroup.GroupCode = utxtCode.Text.Trim

            ObjDTMaterialGroup.GroupName = utxtGroupName.Text.Trim

            Dim dr As DataTableReader = ObjDTMaterialGroup.Save().CreateDataReader

            If dr.Read() Then
                If dr(0).ToString = "0" Then
                    Throw New Exception(dr(1).ToString)
                Else
                    ObjDTMaterialGroup.GroupNo = Convert.ToInt16(dr(1))

                End If
            End If

            dr.Close()
            SaveQC(ObjDTMaterialGroup)
            objBase.CommitTransaction()

            If ugbFastEntry.Visible = False Then
                objBase.SavedSuccessMessage()
                NewRecord()
            End If

            GroupNo = ObjDTMaterialGroup.GroupNo
            ObjDTMaterialGroup = Nothing

        Catch ex As Exception
            objBase.RollbackTransaction()
            objBase.ErrorMessage(ex)
        Finally
            objBase.CloseTransaction()
        End Try
        Return GroupNo
    End Function


    Private Sub SaveQC(ByRef ObjDTMaterialGroup As SpectrumERP.DataLayer.DTMaterialGroup)
        Try
            Dim dr As DataTableReader
            For Each dRow As DataRow In QcGroup.GridDataSource.Rows

                If Val(Convert.ToString(dRow("QC Parameter Name"))) <> 0 Then
                    ObjDTMaterialGroup.QCParameterNo = Convert.ToInt16(dRow("QC Parameter Name"))
                    ObjDTMaterialGroup.StandardValue = Convert.ToDecimal(dRow("Standard Value"))

                    ObjDTMaterialGroup.ToleranceValue = Convert.ToDecimal(dRow("Tolerance Value"))
                    ObjDTMaterialGroup.DeductionRate = Convert.ToByte(dRow("Deduction Rate"))

                    ObjDTMaterialGroup.DeductionType = Convert.ToByte(dRow("Deduction Type"))

                    If String.IsNullOrEmpty(Convert.ToString(dRow("Double Deduction From"))) Then
                        ObjDTMaterialGroup.DoubleDeductionFrom = Nothing
                    Else
                        ObjDTMaterialGroup.DoubleDeductionFrom = CType(dRow("Double Deduction From"), Single)
                    End If

                    dr = ObjDTMaterialGroup.SaveQCParameter.CreateDataReader
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

        If ucmbCategoryName.SelectedRow Is Nothing Then

            If ugbFastEntry.Visible = False Then
                objBase.ValidationMessage("Select valid Category Name.")
                ucmbCategoryName.Focus()
            Else
                strError = "Select valid Category Name."
            End If

            Return False
        End If

        If utxtCode.TextLength <> 2 Then

            If ugbFastEntry.Visible = False Then
                objBase.FormValidation("Code must be 2 digit.")
                utxtCode.Focus()
            Else
                strError = "Code must be 2 digit."
            End If

            Exit Function
        Else

            Dim ObjDTMaterialGroup As New SpectrumERP.DataLayer.DTMaterialGroup()
            ObjDTMaterialGroup.GroupNo = CType(objLocalBase.getId, Short)

            ObjDTMaterialGroup.GroupName = utxtGroupName.Text.Trim
            ObjDTMaterialGroup.CompanyNo = gCompanyNo

            ObjDTMaterialGroup.CategoryNo = Convert.ToInt16(ucmbCategoryName.Value)
            ObjDTMaterialGroup.GroupCode = utxtCode.Text.Trim

            Dim dr As DataTableReader = ObjDTMaterialGroup.Validate().CreateDataReader
            If dr.Read() Then

                If dr(0).ToString = "0" Then
                    If dr(2).ToString = "1" Then ' GROUP NAME DUPLICATE

                        If ugbFastEntry.Visible = False Then
                            objBase.FormValidation(dr(1).ToString)
                            utxtGroupName.Focus()
                        Else
                            strError = Convert.ToString(dr(1))
                        End If

                        Exit Function
                    Else

                        If ugbFastEntry.Visible = False Then
                            objBase.FormValidation(dr(1).ToString) 'DUPLICATE CODE
                            utxtCode.Focus()
                        Else
                            strError = Convert.ToString(dr(1))
                        End If

                        Exit Function
                    End If
                End If
            End If 'END OF DR.READ()
            dr.Close()
        End If 'END OF utxtCode.TextLength 

        If utxtGroupName.Text.Trim = "" Then
            If ugbFastEntry.Visible = False Then

                objBase.ValidationMessage("Enter Group Name.")
                utxtGroupName.Focus()

            Else
                strError = "Enter Group Name."
            End If

            Return False
        End If

        If QcGroup.ValidateForm(Nothing) = False Then
            Return False
        End If

        ValidateForm = True
    End Function

    Private Sub ucmbCategoryName_ValueChanged(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles ucmbCategoryName.ValueChanged
        Try
            utxtCategoryCode.Value = ""
            utxtCode.Text = ""
            utxtGroupCode.Text = ""

            If ucmbCategoryName.SelectedRow IsNot Nothing Then
                'Category Code based on selected Category
                utxtCategoryCode.Value = ucmbCategoryName.SelectedRow.Cells("Code").Value

                '(Group) Code based on selected Category
                Dim ObjDTMaterialGroup As New SpectrumERP.DataLayer.DTMaterialGroup
                ObjDTMaterialGroup.CategoryNo = Convert.ToInt16(ucmbCategoryName.Value)

                Dim dr As DataTableReader = ObjDTMaterialGroup.FillValuesDependent.CreateDataReader
                If dr.Read() Then
                    utxtCode.Value = dr(0)
                End If
                dr.Close()

                'Group Code based on selected Category and Given Group Code
                utxtGroupCode.Value = utxtCategoryCode.Text & utxtCode.Text
            End If


        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try

    End Sub

    Private Sub utxtCode_ValueChanged(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles utxtCode.ValueChanged
        Try
            'Group Code based on selected Category and Given Group Code
            utxtGroupCode.Value = utxtCategoryCode.Text & utxtCode.Text

        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try
    End Sub

    Public Sub Email(ByVal mailTo As String, ByVal subject As String, ByVal body As String) Implements IMDIFunctions.Email

    End Sub

    Public Sub Export() Implements IMDIFunctions.Export

    End Sub

    Private Sub ufllCode_LinkClicked(ByVal sender As System.Object, ByVal e As Infragistics.Win.FormattedLinkLabel.LinkClickedEventArgs) Handles ufllCode.LinkClicked

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

        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try

    End Sub

    Private Sub ugdFastEntry_InitializeLayout(ByVal sender As System.Object, ByVal e As Infragistics.Win.UltraWinGrid.InitializeLayoutEventArgs) Handles ugdFastEntry.InitializeLayout

        Try

            Dim band As UltraGridBand = e.Layout.Bands(0)
            band.Columns("Remarks").CellActivation = Activation.ActivateOnly

            band.Columns("Category Name").Width = 183
            band.Columns("Code").Width = 107

            band.Columns("Group Name").Width = 321
            band.Columns("Remarks").Width = 310

            band.Columns("Group Name").Width = 100
            band.Columns("Code").MaxLength = 2

            objBase.Grd_Formatting(CType(sender, UltraGrid))

        Catch ex As Exception
            objBase.ErrorMessage(ex)
        End Try

    End Sub

End Class