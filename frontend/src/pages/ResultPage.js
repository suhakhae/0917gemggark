// src/pages/ResultPage.js (오류 방어 코드 추가 버전)
import React from 'react';
import { Box, Typography, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Tooltip } from '@mui/material';

const ResultPage = ({ data }) => {
  // [핵심 수정] data.strategy_details가 존재하는지 확인하는 조건을 추가합니다.
  if (!data || data.total_cost === 0 || !data.strategy_details) {
    return (
        <Box sx={{ padding: 2 }}>
            <Typography variant="h5" gutterBottom>최적화 결과</Typography>
            <Typography>계산된 최적의 전략이 없습니다. 입력값을 확인하거나 다시 시도해주세요.</Typography>
        </Box>
    );
  }

  // strategy_details가 비어있는 경우도 처리합니다.
  if (Object.keys(data.strategy_details).length === 0) {
    return (
        <Box sx={{ padding: 2 }}>
            <Typography variant="h5" gutterBottom>최적화 결과</Typography>
            <Typography>총 예상 비용: {data.total_cost.toLocaleString()} Gold</Typography>
            <Typography sx={{marginTop: 2}}>세부 전략이 없습니다.</Typography>
        </Box>
    )
  }

  return (
    <Box sx={{ padding: 2 }}>
      <Typography variant="h5" gutterBottom>최적화 결과</Typography>
      
      <Paper sx={{ padding: 2, marginBottom: 3, backgroundColor: '#f0f4f8' }}>
        <Typography variant="h6">요약</Typography>
        <Typography variant="h4" color="primary">
          총 예상 비용: {data.total_cost.toLocaleString()} Gold
        </Typography>
      </Paper>

      {Object.entries(data.strategy_details).map(([coreType, details]) => (
        <Box key={coreType} sx={{ marginBottom: 3 }}>
          <Typography variant="h6" gutterBottom>{coreType} 코어 전략 (총 {details.total_cost.toLocaleString()} Gold)</Typography>
          {details.details_per_core.map((coreDetail) => (
            <Paper key={coreDetail.core} sx={{ padding: 2, marginBottom: 2 }}>
              <Typography variant="subtitle1" gutterBottom>{coreDetail.core}</Typography>
              <TableContainer component={Paper}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>목표 스펙</TableCell>
                      <TableCell>필요 의지력</TableCell>
                      <TableCell>추천 재료</TableCell>
                      <TableCell align="right">예상 비용 (Gold)</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {coreDetail.best_combination.map((combo, index) => (
                      <TableRow key={index}>
                        <TableCell>{combo.target_spec_str}</TableCell>
                        <TableCell>{combo.willpower_cost}</TableCell>
                        <TableCell>{combo.material_gem}</TableCell>
                        <TableCell align="right">
                          <Tooltip 
                            title={
                              <Box>
                                <Typography>재료비: {combo.breakdown.gem_cost.toLocaleString()}</Typography>
                                <Typography>가공비: {combo.breakdown.craft_cost.toLocaleString()}</Typography>
                                <Typography>페온값: {combo.breakdown.peon_cost.toLocaleString()}</Typography>
                                <Typography>초기화비: {combo.breakdown.initialize_cost.toLocaleString()}</Typography>
                              </Box>
                            }
                          >
                            <Typography sx={{ textDecoration: 'underline dotted' }}>
                              {combo.total_cost.toLocaleString()}
                            </Typography>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          ))}
        </Box>
      ))}
    </Box>
  );
};

export default ResultPage;