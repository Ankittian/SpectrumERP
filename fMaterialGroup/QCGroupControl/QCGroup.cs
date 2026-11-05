using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Drawing;
using System.Data;
using System.Text;
using System.Windows.Forms;
using Infragistics.Win.UltraWinGrid;
using System.Threading;
using BaseArchitecture.BusinessLogicLayer;

namespace QCGroupdll
{
    public partial class QCGroup : UserControl
    {
        #region Private Variables

        bool bIsAllowGridUpdate = true;
        bool bIsLoading = true;

        bool bHideQCGroupCombo = false;
        bool bQCExistsValidation = false, bIsRowEditTemplates = false;

        bool bHideActualValueColumns = true;

        DataTable dtPopulateFields = new DataTable();

        static List<System.Type> lstNumericType = new List<System.Type>();

        Dictionary<string, object> dicUniColValueForDelete = new Dictionary<string, object>();
        Dictionary<string, System.Type> dicUniqueCols = new Dictionary<string, System.Type>();

        UltraGridRowEditTemplate uCtrlRowEditTemplate;
        UltraGrid uCtrlGrid;

        string[] astrUniqueColumnName;
        string[] astrOptionalColumnName;

        string strCtrlOnColumn = "";
        Boolean bIsHideQCDeduction = false;

        #endregion

        #region Public Variables
        public DataTable dtQCParameter = new DataTable();
        #endregion

        delegate void FilterComboListCallBack();
        delegate void FilterComboValuedListCallBack(short CustomFieldNo);
        delegate void FillGridCallBack();

        public QCGroup()
        {
            InitializeComponent();
        }

        #region FillValues
        private void FillGrid()
        {
            if (this.InvokeRequired)
            {
                FillGridCallBack d = new FillGridCallBack(FillGrid);
                this.BeginInvoke(d);
            }
            else
            {
                if (bIsLoading)
                {
                    Datalayer.DTQCGroup ODTQCGroup = new Datalayer.DTQCGroup();

                    ODTQCGroup.CompanyNo = ClsCommonFunction.globalVar.CompanyNo;

                    DataSet ds = ODTQCGroup.FillValues();

                    
                    lstNumericType.Add(typeof(Byte));
                    lstNumericType.Add(typeof(Decimal));
                    lstNumericType.Add(typeof(Double));
                    lstNumericType.Add(typeof(Int16));
                    lstNumericType.Add(typeof(Int32));
                    lstNumericType.Add(typeof(Int64));
                    lstNumericType.Add(typeof(SByte));
                    lstNumericType.Add(typeof(Single));
                    lstNumericType.Add(typeof(UInt16));
                    lstNumericType.Add(typeof(UInt32));
                    lstNumericType.Add(typeof(UInt64));

                    DataTableReader Dr = ds.Tables[12].CreateDataReader();
 
                    if (Dr.Read())
                    {
                        bIsHideQCDeduction =  Convert.ToBoolean(Dr["IsHideQCDeduction"]);
                    }
                    Dr.Close(); 

                    LocalVariables.objBase.GrdSetDataSource(ugdQCGroup, ds.Tables[1]);

                    LocalVariables.objBase.UltraGridColumnText(ugdQCGroup, "Standard Value", 10, BaseArchitecture.BusinessLogicLayer.ClsCommonFunction.EnterType.FloatType,3);
                    LocalVariables.objBase.UltraGridColumnText(ugdQCGroup, "Standard Value2", 10, BaseArchitecture.BusinessLogicLayer.ClsCommonFunction.EnterType.FloatType, 3);

                    LocalVariables.objBase.UltraGridColumnText(ugdQCGroup, "Actual Value1", 10, BaseArchitecture.BusinessLogicLayer.ClsCommonFunction.EnterType.FloatType, 3);
                    LocalVariables.objBase.UltraGridColumnText(ugdQCGroup, "Actual Value2", 10, BaseArchitecture.BusinessLogicLayer.ClsCommonFunction.EnterType.FloatType, 3);

                    LocalVariables.objBase.UltraGridColumnText(ugdQCGroup, "Tolerance Value", 10, BaseArchitecture.BusinessLogicLayer.ClsCommonFunction.EnterType.FloatType, 3);
                    LocalVariables.objBase.UltraGridColumnText(ugdQCGroup, "Double Deduction From", 10, BaseArchitecture.BusinessLogicLayer.ClsCommonFunction.EnterType.FloatType, 3);
                    LocalVariables.objBase.UltraGridColumnDuplicate(ugdQCGroup, new object[] { "QC Parameter Name" }, "Duplicate QC Parameter not allowed.");

                    dtQCParameter = ds.Tables[9];

                    // Add Event
                    if (RowEditTemplate)
                    {
                        uCtrlGrid.BeforeRowEditTemplateDisplayed += ultraGrid_BeforeRowEditTemplateDisplayed;
                        uCtrlGrid.AfterRowsDeleted += UltraGrid_AfterRowsDeleted;
                        uCtrlGrid.AfterCellUpdate += UltraGrid_AfterCellUpdate;
                        uCtrlGrid.BeforeCellUpdate += UltraGrid_BeforeCellUpdate;
                        uCtrlGrid.Disposed += UltraGrid_Disposed;

                        List<string> list = new List<string>(dicUniqueCols.Keys);

                        foreach (string strKeys in list)
                        {
                            dtQCParameter.Columns.Add(strKeys, dicUniqueCols[strKeys]);
                        }
                    }
                    else
                    {
                        RowEditTemplate = bIsRowEditTemplates;
                    }

                    dtPopulateFields = ds.Tables[2];

                    LocalVariables.objBase.FillControls(ds.Tables[0], ucmbQCGroup, new string[] { "QCGroupNo", "QC Group Name", "Code" });
                    LocalVariables.objBase.PopulateValueList(dtPopulateFields, ugdQCGroup, "QC Parameter Name", new string[] { "QCParameterNo", "QC Parameter Name", "Code" });

                    LocalVariables.objBase.PopulateValueList(ds.Tables[3], ugdQCGroup, "Unit", new string[] { "UnitNo", "Unit", "Code" });
                    LocalVariables.objBase.PopulateValueList(ds.Tables[4], ugdQCGroup, "Tolerance Type", new string[] { "ToleranceTypeNo", "Tolerance Type" });

                    LocalVariables.objBase.PopulateValueList(ds.Tables[10], ugdQCGroup, "Tolerance Unit", new string[] { "UnitNo", "Tolerance Unit" });

                    LocalVariables.objBase.PopulateValueList(ds.Tables[5], ugdQCGroup, "Deduction On", new string[] { "ID", "Deduction On" });
                    LocalVariables.objBase.PopulateValueList(ds.Tables[6], ugdQCGroup, "Formula Type", new string[] { "ID", "Formula Type" });

                    LocalVariables.objBase.PopulateValueList(ds.Tables[7], ugdQCGroup, "Deduction Rate", new string[] { "Id", "Deduction Rate" });
                    LocalVariables.objBase.PopulateValueList(ds.Tables[8], ugdQCGroup, "Deduction Type", new string[] { "Id", "Deduction Type" });

                    ugdQCGroup.ActiveCell = ugdQCGroup.Rows[0].Cells["QC Parameter Name"];
                    LocalVariables.objBase.FilterValueList(ugdQCGroup, "Inactive", 0);
                    
                    bIsLoading = false;
                }
            }
        }
        public void FillValues()
        {

            try
            {

                lock ((LocalVariables.objLock))
                {

                    FillGrid();
                    FilterComboList();
                }
            }
            catch (Exception ex)
            {
                if ((ex) is ThreadAbortException)
                {
                }
                else
                {
                    LocalVariables.objBase.ErrorMessage(ex.Message);
                }
            }
        }
        /// <summary>
        /// Fill Values,when using custom control as RowEditTemplate
        /// </summary>
        /// <param name="uGrid">Parent Grid of RowEditTemplate </param>
        /// <param name="uRowEditTemplate">RowEditTemplate Name</param>
        /// <param name="dicUniqueColumns">Unique Columns of Parent Grid </param>
        /// <param name="strOnColumn">Show RowTemplate,on action of this Column</param>
        public void FillValues(UltraGrid ParentUltraGrid, UltraGridRowEditTemplate uRowEditTemplate
            , string[] UniqueColumn, string[] OptionalColumn
            , Dictionary<string, System.Type> UniqueColumns
            , string OnColumn
            )
        {
            dicUniqueCols.Clear();

            dicUniqueCols = UniqueColumns;
            uCtrlRowEditTemplate = uRowEditTemplate;

            uCtrlGrid = ParentUltraGrid;
            strCtrlOnColumn = OnColumn;

            astrUniqueColumnName = UniqueColumn;
            astrOptionalColumnName = OptionalColumn;
            FillValues();
        }


        #endregion


        #region Control Load Event

        private void QCGroup_Load(object sender, EventArgs e)
        {
            //bIsLoading = true;             

            if (!bIsRowEditTemplates)
            {
                ubtnOK.Visible = false;
                ubtnCancel.Visible = false;
            }
        }
        #endregion

        #region GridEvents

        private void ugdQCGroup_InitializeLayout(object sender, InitializeLayoutEventArgs e)
        {
            e.Layout.Bands[0].Columns["Unit"].CellActivation = Activation.NoEdit;
            e.Layout.Bands[0].Columns["Tolerance Unit"].CellActivation = Activation.NoEdit;

            e.Layout.Bands[0].Columns["Deduction On"].CellActivation = Activation.NoEdit;
            e.Layout.Bands[0].Columns["Formula Type"].CellActivation = Activation.NoEdit;

            e.Layout.Bands[0].Columns["Tolerance Type"].CellActivation = Activation.NoEdit;            

            //------------------------------------ Width of columns -----------------------
            e.Layout.Bands[0].Columns["Unit"].Width = 60;

            e.Layout.Bands[0].Columns["Standard Value"].Width = 60;
            e.Layout.Bands[0].Columns["Standard Value2"].Width = 60;

            e.Layout.Bands[0].Columns["Actual Value1"].Width = 60;
            e.Layout.Bands[0].Columns["Actual Value2"].Width = 60;

            e.Layout.Bands[0].Columns["Tolerance Value"].Width = 70;
            e.Layout.Bands[0].Columns["Tolerance Type"].Width = 65;
            e.Layout.Bands[0].Columns["Tolerance Unit"].Width = 65;

            e.Layout.Bands[0].Columns["Deduction Rate"].Width = 70;

            e.Layout.Bands[0].Columns["Formula Type"].Width = 60;
            e.Layout.Bands[0].Columns["Deduction Type"].Width = 70;

            e.Layout.Bands[0].Columns["Double Deduction From"].Width = 70;

            //----------------------------- Rename -----------------------------
            e.Layout.Bands[0].Columns["Standard Value"].Header.Caption = "Standard Value1";

            //----------------------------- Hidden ----------------------------------
            e.Layout.Bands[0].Columns["Actual Value1"].Hidden = bHideActualValueColumns;
            e.Layout.Bands[0].Columns["Actual Value2"].Hidden = bHideActualValueColumns;


            FilterComboList();

            if (bIsHideQCDeduction == true)
            {
                e.Layout.Bands[0].Columns["Deduction On"].Hidden = true;
                    
                e.Layout.Bands[0].Columns["Deduction Rate"].Hidden = true;

                e.Layout.Bands[0].Columns["Formula Type"].Hidden = true;
                e.Layout.Bands[0].Columns["Deduction Type"].Hidden = true;

                e.Layout.Bands[0].Columns["Double Deduction From"].Hidden = true;
            }
            else
            {
                e.Layout.Bands[0].Columns["Deduction On"].Hidden = false;
                e.Layout.Bands[0].Columns["Deduction Rate"].Hidden = false;

                e.Layout.Bands[0].Columns["Formula Type"].Hidden = false;
                e.Layout.Bands[0].Columns["Deduction Type"].Hidden = false;

                e.Layout.Bands[0].Columns["Double Deduction From"].Hidden = false;
            } 

            LocalVariables.objBase.Grd_Formatting(ugdQCGroup);
        }

        private void ugdQCGroup_BeforeCellActivate(object sender, CancelableCellEventArgs e)
        {
            if (e.Cell.Column.Key == "Double Deduction From")
            {
                if (Convert.ToString(e.Cell.Row.GetCellValue(ugdQCGroup.DisplayLayout.Bands[0].Columns["Deduction Type"])) == "1")
                    e.Cell.Row.Cells["Double Deduction From"].Activation = Activation.NoEdit;
                else
                    e.Cell.Row.Cells["Double Deduction From"].Activation = Activation.AllowEdit;
            }
        }

        private void ugdQCGroup_AfterCellUpdate(object sender, CellEventArgs e)
        {
            if (e.Cell.Row.Index == ugdQCGroup.Rows.Count - 1)
            {
                ugdQCGroup.Rows.Band.AddNew();
            }

            if (e.Cell.Column.Key == "Deduction Type")
            {
                if (Convert.ToString(e.Cell.Row.GetCellValue(ugdQCGroup.DisplayLayout.Bands[0].Columns["Deduction Type"])) == "1")
                {
                    e.Cell.Row.Cells["Double Deduction From"].Value = DBNull.Value;
                }
            }
            else if (e.Cell.Column.Key == "QC Parameter Name")
            {
                UltraGridRow ugdRow;
                ugdRow = LocalVariables.objBase.Cell_ValueListResolved(e.Cell);


                if (ugdRow != null)
                {
                    e.Cell.Row.Cells["Unit"].Value = ugdRow.Cells["UnitNo"].Value;
                    e.Cell.Row.Cells["Standard Value"].Value = ugdRow.Cells["StandardValue"].Value;
                    e.Cell.Row.Cells["Standard Value2"].Value = ugdRow.Cells["StandardValue2"].Value;
                    e.Cell.Row.Cells["Actual Value1"].Value = ugdRow.Cells["ActualValue1"].Value;
                    e.Cell.Row.Cells["Actual Value2"].Value = ugdRow.Cells["ActualValue2"].Value;
                    e.Cell.Row.Cells["Tolerance Value"].Value = ugdRow.Cells["ToleranceValue"].Value;
                    e.Cell.Row.Cells["Tolerance Type"].Value = ugdRow.Cells["ToleranceType"].Value;
                    e.Cell.Row.Cells["Tolerance Unit"].Value = ugdRow.Cells["ToleranceUnit"].Value;
                    e.Cell.Row.Cells["Deduction On"].Value = ugdRow.Cells["DeductionOn"].Value;
                    e.Cell.Row.Cells["Formula Type"].Value = ugdRow.Cells["FormulaType"].Value;
                    e.Cell.Row.Cells["Deduction Rate"].Value = ugdRow.Cells["DeductionRate"].Value;
                    e.Cell.Row.Cells["Deduction Type"].Value = ugdRow.Cells["DeductionType"].Value;
                    e.Cell.Row.Cells["Double Deduction From"].Value = ugdRow.Cells["DoubleDeductionFrom"].Value;
                }
                else
                {
                    e.Cell.Row.Cells["Unit"].Value = DBNull.Value;
                    e.Cell.Row.Cells["Standard Value"].Value = DBNull.Value;
                    e.Cell.Row.Cells["Standard Value2"].Value = DBNull.Value;
                    e.Cell.Row.Cells["Actual Value1"].Value = DBNull.Value ;
                    e.Cell.Row.Cells["Actual Value2"].Value = DBNull.Value;
                    e.Cell.Row.Cells["Tolerance Value"].Value = DBNull.Value;
                    e.Cell.Row.Cells["Tolerance Type"].Value = DBNull.Value;
                    e.Cell.Row.Cells["Tolerance Unit"].Value = DBNull.Value;
                    e.Cell.Row.Cells["Deduction On"].Value = DBNull.Value;
                    e.Cell.Row.Cells["Formula Type"].Value = DBNull.Value;
                    e.Cell.Row.Cells["Deduction Rate"].Value = DBNull.Value;
                    e.Cell.Row.Cells["Deduction Type"].Value = DBNull.Value;
                    e.Cell.Row.Cells["Double Deduction From"].Value = DBNull.Value;
                }

            }
        }

        #endregion

        #region Combo Value Changed

        private void ucmbQCGroup_ValueChanged(object sender, EventArgs e)
        {
            Datalayer.DTQCGroup oDTQCGroup = new Datalayer.DTQCGroup();
            oDTQCGroup.QCGroupNo = Convert.ToInt16(ucmbQCGroup.Value);
            oDTQCGroup.CompanyNo = ClsCommonFunction.globalVar.CompanyNo;

            DataSet ds = oDTQCGroup.FillValuesDependent();
            LocalVariables.objBase.GrdSetDataSource(ugdQCGroup, ds.Tables[0]);
        }
        #endregion

        #region ValidateForm
        public bool ValidateForm(Infragistics.Win.UltraWinTabControl.UltraTab uTab)
        {
            bool bIsFound = false;
            ugdQCGroup.UpdateData();

            foreach (UltraGridRow ugRow in ugdQCGroup.Rows)
            {

                if (Convert.ToString(ugRow.Cells["QC Parameter Name"].Value) != "")
                {
                    if (val(Convert.ToString(ugRow.Cells["Standard Value"].Value)) == 0)
                    {
                        LocalVariables.objBase.Validate(ugRow.Cells["Standard Value"], "Standard Value can't be empty or zero", uTab);
                        return false;
                    }

                    if (val(Convert.ToString(ugRow.Cells["Actual Value1"].Value)) == 0 && ugdQCGroup.DisplayLayout.Bands[0].Columns["Actual Value1"].Hidden==false )
                    {
                        LocalVariables.objBase.Validate(ugRow.Cells["Actual Value1"], "Actual Value1 can't be empty or zero", uTab);
                        return false;
                    }

                    if (Convert.ToString(ugRow.Cells["Tolerance Value"].Value) == "")
                    {
                        LocalVariables.objBase.Validate(ugRow.Cells["Tolerance Value"], "Enter Tolerance Value", uTab);
                        return false;
                    }

                    if (Convert.ToString(ugRow.Cells["Deduction Rate"].Value) == "")
                    {
                        LocalVariables.objBase.Validate(ugRow.Cells["Deduction Rate"], "Select valid Deduction Rate", uTab);
                        return false;
                    }

                    if (Convert.ToString(ugRow.Cells["Deduction Type"].Value) == "")
                    {
                        LocalVariables.objBase.Validate(ugRow.Cells["Deduction Type"], "Select valid Deduction Type", uTab);
                        return false;
                    }

                    if (Convert.ToString(ugRow.Cells["Deduction Type"].Value) == "2")
                    {
                        if (Convert.ToString(ugRow.Cells["Double Deduction From"].Value) == "")
                        {
                            LocalVariables.objBase.Validate(ugRow.Cells["Double Deduction From"], "Enter Double Deduction From", uTab);
                            return false;
                        }
                    }
                    bIsFound = true;
                }
            }

            if (!(bIsFound) && bQCExistsValidation)
            {
                LocalVariables.objBase.ValidationMessage("Select atleast one QC Parameter.");
                if (uTab != null)
                {
                    uTab.Selected = true;
                }
                ugdQCGroup.Focus();
                return false;
            }
            return true;
        }
        #endregion

        #region Events (Event Handler)

        private void UltraGrid_Disposed(System.Object sender, System.EventArgs e)
        {
            ((UltraGrid)sender).BeforeRowEditTemplateDisplayed -= ultraGrid_BeforeRowEditTemplateDisplayed;
            ((UltraGrid)sender).AfterCellUpdate -= UltraGrid_AfterCellUpdate;
            ((UltraGrid)sender).BeforeCellUpdate -= UltraGrid_BeforeCellUpdate;
            ((UltraGrid)sender).AfterRowsDeleted -= UltraGrid_AfterRowsDeleted;
            ((UltraGrid)sender).Disposed -= UltraGrid_Disposed;
        }

        private void ultraGrid_BeforeRowEditTemplateDisplayed(object sender, Infragistics.Win.UltraWinGrid.BeforeRowEditTemplateDisplayedEventArgs e)
        {
            UltraGridCell uCell = uCtrlGrid.ActiveCell;
            if (uCell == null)
            {
                return;
            }



            if (uCell.Column.Key.ToString() == strCtrlOnColumn)
            {
                if (!LocalVariables.objBase.GrdColumnDuplicacyValdation(uCtrlGrid, astrUniqueColumnName, astrOptionalColumnName, true, ""))
                {
                    e.Cancel = true;
                    return;
                }

                if (!BeforeRowEditTemplateDisplayed())
                {
                    e.Cancel = true;
                }

            }
        }

        private void UltraGrid_AfterCellUpdate(object sender, CellEventArgs e)
        {
            if (e.Cell == null)
            {
                return;
            }

            List<string> list = new List<string>(dicUniColValueForDelete.Keys);

            if (list.Contains(e.Cell.Column.Key))
            {
                DeletedtRows();
            }

        }
        private void UltraGrid_BeforeCellUpdate(object sender, BeforeCellUpdateEventArgs e)
        {
            if (e.Cell == null)
            {
                return;
            }


            List<string> list = new List<string>(dicUniqueCols.Keys);

            if (list.Contains(e.Cell.Column.Key))
            {
                dicUniColValueForDelete.Clear();
                foreach (string strKeys in list)
                {
                    switch (GetType(dicUniqueCols[strKeys]))
                    {
                        case 1:
                            dicUniColValueForDelete.Add(strKeys, val(e.Cell.Row.GetCellValue(uCtrlGrid.DisplayLayout.Bands[0].Columns[strKeys])));
                            break;
                        case 2:
                            dicUniColValueForDelete.Add(strKeys, e.Cell.Row.GetCellValue(uCtrlGrid.DisplayLayout.Bands[0].Columns[strKeys]));
                            break;
                    }
                }
            }
        }

        private void UltraGrid_AfterRowsDeleted(object sender, EventArgs e)
        {
            uCtrlGrid.UpdateData();
            dtQCParameter.AcceptChanges();
            if (uCtrlGrid.DataSource == null)
            {
                return;
            }

            string strFilter = "";
            List<string> list = new List<string>(dicUniqueCols.Keys);

            foreach (DataRow dRow in dtQCParameter.Rows)
            {
                strFilter = "";
                foreach (string strKeys in list)
                {
                    switch (GetType(dicUniqueCols[strKeys]))
                    {
                        case 1:
                            strFilter = strFilter + " and " + "Isnull([" + strKeys + "],0)=" + val(dRow[strKeys]);
                            break;
                        case 2:
                            strFilter = strFilter + " and " + "IsNull([" + strKeys + "],'')='" + Convert.ToString(dRow[strKeys]) + "'";
                            break;
                    }
                }

                if (((DataTable)uCtrlGrid.DataSource).Select(strFilter.Substring(4)).Length == 0)
                {
                    dRow.Delete();
                }
            }

            dtQCParameter.AcceptChanges();
        }

        #endregion

        #region BeforeRowEditTemplateDisplayed

        public bool BeforeRowEditTemplateDisplayed()
        {
            dtQCParameter.AcceptChanges();
            ucmbQCGroup.Value = null;
            bool bIsFound = false;
            List<string> list = new List<string>(dicUniqueCols.Keys);

            foreach (string strKeys in list)
            {
                if (!(string.IsNullOrEmpty(Convert.ToString(uCtrlGrid.ActiveRow.Cells[strKeys].Value))))
                {
                    bIsFound = true;
                }
            }

            if (bIsFound)
            {
                string strFilter = GetFilterString();
                int i = 0;

                LocalVariables.objBase.RefreshForm(ugdQCGroup);

                foreach (DataRow drow in dtQCParameter.Select(strFilter))
                {
                    ugdQCGroup.Rows[i].Cells["QC Parameter Name"].Value = drow["QC Parameter Name"];
                    ugdQCGroup.Rows[i].Cells["Unit"].Value = drow["Unit"];
                    ugdQCGroup.Rows[i].Cells["Standard Value"].Value = drow["Standard Value"];
                    ugdQCGroup.Rows[i].Cells["Standard Value2"].Value = drow["Standard Value2"];
                    ugdQCGroup.Rows[i].Cells["Actual Value1"].Value = drow["Actual Value1"];
                    ugdQCGroup.Rows[i].Cells["Actual Value2"].Value = drow["Actual Value2"];
                    ugdQCGroup.Rows[i].Cells["Tolerance Value"].Value = drow["Tolerance Value"];
                    ugdQCGroup.Rows[i].Cells["Tolerance Type"].Value = drow["Tolerance Type"];
                    ugdQCGroup.Rows[i].Cells["Tolerance Unit"].Value = drow["Tolerance Unit"];
                    ugdQCGroup.Rows[i].Cells["Deduction On"].Value = drow["Deduction On"];
                    ugdQCGroup.Rows[i].Cells["Formula Type"].Value = drow["Formula Type"];
                    ugdQCGroup.Rows[i].Cells["Deduction Rate"].Value = drow["Deduction Rate"];
                    ugdQCGroup.Rows[i].Cells["Deduction Type"].Value = drow["Deduction Type"];
                    ugdQCGroup.Rows[i].Cells["Double Deduction From"].Value = drow["Double Deduction From"];
                    i++;
                }
                FilterComboList();
            }
            return bIsFound;
        }
        #endregion

        #region ButtonclickEvents

        private void ubtnCancel_Click(object sender, EventArgs e)
        {
            uCtrlRowEditTemplate.Close();
        }

        private void ubtnOK_Click(object sender, EventArgs e)
        {
            ugdQCGroup.UpdateData();
            dtQCParameter.AcceptChanges();

            if (ValidateForm(null) == false)
            {
                return;
            }

            foreach (DataRow drow in dtQCParameter.Select(GetFilterString()))
            {
                drow.Delete();
            }


            List<string> list = new List<string>(dicUniqueCols.Keys);

            List<object> lstUniqueColData = new List<object>();
            List<object> lstRowEditData = new List<object>();

            foreach (string strKeys in list)
            {
                switch (GetType(dicUniqueCols[strKeys]))
                {
                    case 1:
                        if (Convert.ToString(uCtrlGrid.ActiveRow.Cells[strKeys].Value) == "")
                        {
                            lstUniqueColData.Add(null);
                        }
                        else
                        {
                            lstUniqueColData.Add(uCtrlGrid.ActiveRow.Cells[strKeys].Value);
                        }

                        break;
                    case 2:
                        lstUniqueColData.Add(uCtrlGrid.ActiveRow.Cells[strKeys].Value);
                        break;
                    default:
                        lstUniqueColData.Add(uCtrlGrid.ActiveRow.Cells[strKeys].Value);
                        break;
                }

            }

            foreach (UltraGridRow ugdRow in ugdQCGroup.Rows)
            {
                lstRowEditData.Clear();
                if (!(string.IsNullOrEmpty(Convert.ToString(ugdRow.GetCellValue(ugdQCGroup.DisplayLayout.Bands[0].Columns["QC Parameter Name"])))))
                {
                    lstRowEditData.Add(ugdRow.GetCellValue(ugdQCGroup.DisplayLayout.Bands[0].Columns["QC Parameter Name"]));
                    lstRowEditData.Add(ugdRow.GetCellValue(ugdQCGroup.DisplayLayout.Bands[0].Columns["Unit"]));
                    lstRowEditData.Add(ugdRow.GetCellValue(ugdQCGroup.DisplayLayout.Bands[0].Columns["Standard Value"]));
                    lstRowEditData.Add(ugdRow.GetCellValue(ugdQCGroup.DisplayLayout.Bands[0].Columns["Standard Value2"]));
                    lstRowEditData.Add(ugdRow.GetCellValue(ugdQCGroup.DisplayLayout.Bands[0].Columns["Actual Value1"]));
                    lstRowEditData.Add(ugdRow.GetCellValue(ugdQCGroup.DisplayLayout.Bands[0].Columns["Actual Value2"]));
                    lstRowEditData.Add(ugdRow.GetCellValue(ugdQCGroup.DisplayLayout.Bands[0].Columns["Tolerance Value"]));
                    lstRowEditData.Add(ugdRow.GetCellValue(ugdQCGroup.DisplayLayout.Bands[0].Columns["Tolerance Type"]));                    
                    lstRowEditData.Add(ugdRow.GetCellValue(ugdQCGroup.DisplayLayout.Bands[0].Columns["Tolerance Unit"]));
                    lstRowEditData.Add(ugdRow.GetCellValue(ugdQCGroup.DisplayLayout.Bands[0].Columns["Deduction On"]));
                    lstRowEditData.Add(ugdRow.GetCellValue(ugdQCGroup.DisplayLayout.Bands[0].Columns["Formula Type"]));
                    lstRowEditData.Add(ugdRow.GetCellValue(ugdQCGroup.DisplayLayout.Bands[0].Columns["Deduction Rate"]));
                    lstRowEditData.Add(ugdRow.GetCellValue(ugdQCGroup.DisplayLayout.Bands[0].Columns["Deduction Type"]));
                    lstRowEditData.Add(ugdRow.GetCellValue(ugdQCGroup.DisplayLayout.Bands[0].Columns["Double Deduction From"]));

                    lstRowEditData.AddRange(lstUniqueColData);
                    dtQCParameter.Rows.Add(lstRowEditData.ToArray());
                }
            }
            LocalVariables.objBase.RefreshForm(ugdQCGroup);
            ucmbQCGroup.Value = null;
            uCtrlRowEditTemplate.Close();
        }
        #endregion

        #region Properties

        /// <summary>
        /// when this property is true,Visibility of QC Group combo will be false
        /// </summary>
        /// 
        [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
        public bool HideQCGroupCombo
        {
            get { return bHideQCGroupCombo; }
            set
            {
                if (value)
                {
                    ucmbQCGroup.Visible = false;
                    ulblQCGroup.Visible = false;
                }
                else
                {
                    ucmbQCGroup.Visible = true;
                    ulblQCGroup.Visible = true;
                    ucmbQCGroup.BringToFront();
                    ulblQCGroup.BringToFront();
                }
                bHideQCGroupCombo = value;
                SetGridPosition();
            }
        }
        /// <summary>
        /// X Coordinate of 'QC Group Name' Combo
        /// </summary>
        /// 
        [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
        public int QCGroupComboLocationX
        {
            get { return ucmbQCGroup.Location.X; }
            set
            {
                ucmbQCGroup.Location = new System.Drawing.Point(value, ucmbQCGroup.Location.Y);
            }
        }

        /// <summary>
        ///  get,set width of 'QC Group Name' combo
        /// </summary>
        /// 
        [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
        public int QCGroupComboWidth
        {
            get { return ucmbQCGroup.Size.Width; }
            set
            {
                ucmbQCGroup.Size = new System.Drawing.Size(value, ucmbQCGroup.Size.Height);
            }
        }
        /// <summary>
        /// When this property is true
        /// </summary>
        /// 
        [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
        public bool QCExistsValidation
        {
            get { return bQCExistsValidation; }
            set
            {
                bQCExistsValidation = value;
            }

        }
        /// <summary>
        /// 
        /// </summary>
        /// 
        [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
        public bool RowEditTemplate
        {
            get
            {
                lock (LocalVariables.objLock)
                {
                    return bIsRowEditTemplates;
                }
            }
            set
            {
                lock (LocalVariables.objLock)
                {
                    if (value)
                    {
                        ubtnCancel.Visible = true;
                        ubtnOK.Visible = true;
                    }
                    else
                    {
                        ubtnCancel.Visible = false;
                        ubtnOK.Visible = false;
                    }
                    bIsRowEditTemplates = value;
                    SetGridPosition();
                }
            }

        }

        [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
        [Browsable(false)]
        public DataTable GridDataSource
        {
            get
            {
                ugdQCGroup.UpdateData();
                DataTable dtQCGroupTemp = ((DataTable)ugdQCGroup.DataSource);
                dtQCGroupTemp.AcceptChanges();
                return dtQCGroupTemp;
            }
            set
            {
                LocalVariables.objBase.GrdSetDataSource(ugdQCGroup, value);
            }
        }

        [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
        [Browsable(false)]
        public bool GridAllowUpdate
        {
            get
            {
                return bIsAllowGridUpdate;
            }
            set
            {
                if (value == true)
                {
                    ugdQCGroup.DisplayLayout.Override.AllowUpdate = Infragistics.Win.DefaultableBoolean.True;
                }
                else
                {
                    ugdQCGroup.DisplayLayout.Override.AllowUpdate = Infragistics.Win.DefaultableBoolean.False;
                }
                bIsAllowGridUpdate = value;
            }
        }

        [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]        
        public bool HideActualValueColumns
        {
            get
            {
                return bHideActualValueColumns;
            }
            set
            {
                bHideActualValueColumns = value;
            }
        }

        #endregion

        #region utility

        void SetGridPosition()
        {
            int iCtrlHeight = 12;
            int SizeY;

            if (HideQCGroupCombo)
            {
                SizeY = 6;
            }
            else
            {
                SizeY = 33;
                iCtrlHeight = iCtrlHeight + 27;
            }

            if (RowEditTemplate)
            {
                iCtrlHeight = iCtrlHeight + 25;
            }


            ugdQCGroup.Location = new System.Drawing.Point(6, SizeY);
            ugdQCGroup.Size = new System.Drawing.Size(ugdQCGroup.Size.Width, ugbQCGroup.Size.Height - iCtrlHeight);

        }

        string GetFilterString()
        {
            string strFilter = "";
            List<string> list = new List<string>(dicUniqueCols.Keys);

            foreach (string strKeys in list)
            {
                switch (GetType(dicUniqueCols[strKeys]))
                {
                    case 1:
                        strFilter = strFilter + " and " + "Isnull([" + strKeys + "],0)=" + val(uCtrlGrid.ActiveRow.Cells[strKeys].Value) + "";
                        break;
                    case 2:
                        strFilter = strFilter + " and " + "IsNull([" + strKeys + "],'')='" + Convert.ToString(uCtrlGrid.ActiveRow.Cells[strKeys].Value) + "'";
                        break;
                }
            }
            return strFilter.Substring(4);
        }

        static int GetType(System.Type ColType)
        {
            if (lstNumericType.Contains(ColType))
            {
                return 1;
            }
            else if (ColType == typeof(String))
            {
                return 2;
            }
            return 0;
        }

        double val(object NumValue)
        {
            if (String.IsNullOrEmpty(Convert.ToString(NumValue)))
            {
                return 0;
            }
            else
            {
                return Convert.ToDouble(Convert.ToString(NumValue));
            }
        }

        void DeletedtRows()
        {
            string strFilter = "";

            List<string> list = new List<string>(dicUniqueCols.Keys);

            foreach (string strKeys in list)
            {
                switch (GetType(dicUniqueCols[strKeys]))
                {
                    case 1:
                        strFilter = strFilter + " and " + "Isnull([" + strKeys + "],0)=" + val(dicUniColValueForDelete[strKeys]) + "";
                        break;
                    case 2:
                        strFilter = strFilter + " and " + "IsNull([" + strKeys + "],'')='" + Convert.ToString(dicUniColValueForDelete[strKeys]) + "'";
                        break;
                }
            }

            foreach (DataRow drow in dtQCParameter.Select(strFilter.Substring(4)))
            {
                drow.Delete();
            }
            dtQCParameter.AcceptChanges();
        }

        public void reset()
        {
            dtQCParameter.Rows.Clear();
            dicUniColValueForDelete.Clear();
        }
        #endregion

        #region FilterValueList

        void FilterComboList()
        {
            if (this.InvokeRequired)
            {
                FilterComboListCallBack d = new FilterComboListCallBack(FilterComboList);
                this.BeginInvoke(d);
            }
            else
            {
                ugdQCGroup.UpdateData();
                if (ugdQCGroup.DataSource != null)
                {
                    foreach (UltraGridRow ugRowCustField in ugdQCGroup.Rows)
                    {
                        if (Convert.ToString(ugRowCustField.GetCellValue(ugdQCGroup.DisplayLayout.Bands[0].Columns["QC Parameter Name"])) != "")
                        {
                            FilterComboList(Convert.ToInt16(ugRowCustField.GetCellValue(ugdQCGroup.DisplayLayout.Bands[0].Columns["QC Parameter Name"])));
                        }
                    }
                }
            }
        }
        void FilterComboList(short CustomFieldNo)
        {
            if (this.InvokeRequired)
            {
                FilterComboValuedListCallBack d = new FilterComboValuedListCallBack(FilterComboList);
                this.BeginInvoke(d);
            }
            else
            {
                foreach (DataRow dRowCustomField in dtPopulateFields.Select("[QCParameterNo] = " +
                            Convert.ToString(CustomFieldNo) + " And Inactive=1"
                            ))
                {
                    dRowCustomField["Inactive"] = 0;
                }
                dtPopulateFields.AcceptChanges();
            }

        }
        #endregion


        private void ucmbQCGroup_KeyDown(object sender, KeyEventArgs e)
        {
            LocalVariables.objBase.FormKeyDown(ucmbQCGroup.Controls[0], e, ucmbQCGroup);
            if (e.KeyCode == Keys.Escape)
                uCtrlRowEditTemplate.Close();
        }

        private void ugdQCGroup_KeyDown(object sender, KeyEventArgs e)
        {
            LocalVariables.objBase.FormKeyDown(ugdQCGroup, e, ugdQCGroup);
        }

        private void ubtnOK_KeyDown(object sender, KeyEventArgs e)
        {
            LocalVariables.objBase.FormKeyDown(ubtnOK, e, ubtnOK);
        }

        private void ubtnCancel_KeyDown(object sender, KeyEventArgs e)
        {
            LocalVariables.objBase.FormKeyDown(ubtnCancel, e, ubtnCancel);
        }

    }
}